"""
app/services/live_service.py
─────────────────────────────
Live price streaming services for Upstox and eToro.

Architecture
────────────
  Client ←── FastAPI WebSocket ─── LiveService ─── Broker REST API (1-3 s poll)

Upstox
  Source  : GET /v2/market-quote/ltp?instrument_key=NSE_EQ|INE848E01016,...
  Interval: UPSTOX_POLL_INTERVAL  (default 1 s)
  Keys    : Upstox instrument keys, e.g. "NSE_EQ|INE848E01016"

  ── Native Upstox WebSocket alternative (not implemented here) ──────────────
  Upstox also provides a binary Protobuf WebSocket feed:
    1. GET /v2/feed/market-data-feed/authorize  →  authorizedRedirectUri
    2. Connect via ``websockets`` to that URI with the Bearer token header
    3. Subscribe:
         {"guid": "...", "method": "sub",
          "data": {"mode": "ltpc", "instrumentKeys": ["NSE_EQ|INE848E01016"]}}
    4. Decode each binary frame with the Upstox Protobuf schema
       (MarketDataFeed_pb2.FeedResponse — available in upstox-python-sdk on PyPI)
  This REST-poll approach gives equivalent 1-second resolution without the
  Protobuf/websockets dependency overhead.
  ────────────────────────────────────────────────────────────────────────────

eToro
  Source  : GET /api/v1/market-data/instruments/rates?instrumentIds=100001,...
  Interval: ETORO_POLL_INTERVAL  (default 3 s — respect rate limits)
  Keys    : str(instrumentId), e.g. "100001"

  eToro has no WebSocket or streaming endpoint; the rates API is the only
  real-time price source available via the Public API.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import AsyncGenerator

import httpx

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)

UPSTOX_POLL_INTERVAL: float = 1.0   # seconds between Upstox LTP polls
ETORO_POLL_INTERVAL: float = 5.0    # seconds between eToro rate polls (respect rate limits)
_ETORO_429_DEFAULT_BACKOFF: float = 10.0  # fallback wait when Retry-After header is absent


# ── Upstox ────────────────────────────────────────────────────────────────────


class UpstoxLiveService:
    """
    Streams live LTP from Upstox by polling the market-quote/ltp REST endpoint.

    Yielded message shape (success)::

        {
          "broker": "upstox",
          "ticks": {
            "NSE_EQ|INE848E01016": {"ltp": 1234.5, "close": 1230.0, "ts": 1746567890.1},
            ...
          },
          "ts": 1746567890.1
        }

    Yielded message shape (error)::

        {"broker": "upstox", "error": "...", "ts": 1746567890.1}
    """

    def __init__(self) -> None:
        s = get_settings()
        self._access_token = s.upstox_access_token
        self._base_url = s.upstox_base_url

    async def _fetch_ltp(
        self, client: httpx.AsyncClient, instrument_keys: list[str]
    ) -> dict:
        """
        Call GET /v2/market-quote/ltp for a batch of instrument keys.

        Returns the ``data`` dict keyed by instrument_key::

            {
              "NSE_EQ|INE848E01016": {
                "last_price": 1234.5,
                "ohlc": {"close": 1230.0, "open": ..., "high": ..., "low": ...}
              },
              ...
            }
        """
        url = f"{self._base_url}/market-quote/ltp"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
        }
        # Upstox accepts a comma-separated instrument_key query param
        params = {"instrument_key": ",".join(instrument_keys)}
        response = await client.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("data", {})

    async def stream(
        self, instrument_keys: list[str]
    ) -> AsyncGenerator[dict, None]:
        """
        Infinite async generator that yields LTP tick dicts every
        ``UPSTOX_POLL_INTERVAL`` seconds until the caller stops iterating.
        """
        async with httpx.AsyncClient() as client:
            while True:
                ts = time.time()
                try:
                    data = await self._fetch_ltp(client, instrument_keys)
                    ticks = {
                        key: {
                            "ltp": info.get("last_price"),
                            "close": info.get("ohlc", {}).get("close"),
                            "ts": ts,
                        }
                        for key, info in data.items()
                    }
                    yield {"broker": "upstox", "ticks": ticks, "ts": ts}
                except httpx.HTTPStatusError as exc:
                    logger.warning(
                        "Upstox LTP HTTP %s error: %s",
                        exc.response.status_code,
                        exc,
                    )
                    yield {"broker": "upstox", "error": str(exc), "ts": ts}
                except Exception as exc:
                    logger.warning("Upstox LTP fetch error: %s", exc)
                    yield {"broker": "upstox", "error": str(exc), "ts": ts}
                await asyncio.sleep(UPSTOX_POLL_INTERVAL)


# ── eToro ─────────────────────────────────────────────────────────────────────


class EToroLiveService:
    """
    Streams live bid/ask rates from eToro by polling
    GET /api/v1/market-data/instruments/rates.

    eToro has no WebSocket feed; the rates endpoint is the only real-time
    price source available via the Public API.

    instrument_keys are ``str(instrumentId)`` integers, e.g. ``["100001", "1001"]``.
    Pass an empty list to stream all held instruments (keys are resolved
    automatically by the WebSocket endpoint via broker holdings).

    Yielded message shape (success)::

        {
          "broker": "etoro",
          "ticks": {
            "100001": {"bid": 1234.5, "ask": 1235.0, "ts": 1746567890.1},
            ...
          },
          "ts": 1746567890.1
        }

    Yielded message shape (error)::

        {"broker": "etoro", "error": "...", "ts": 1746567890.1}
    """

    def __init__(self) -> None:
        s = get_settings()
        self._api_key = s.etoro_api_key
        self._user_key = s.etoro_user_key
        self._base_url = s.etoro_base_url

    def _auth_headers(self) -> dict[str, str]:
        """Build the three required eToro request headers (fresh UUID per call)."""
        return {
            "x-api-key": self._api_key,
            "x-user-key": self._user_key,
            "x-request-id": str(uuid.uuid4()),
            "Accept": "application/json",
        }

    async def _fetch_rates(
        self, client: httpx.AsyncClient, instrument_ids: list[str]
    ) -> dict[str, dict]:
        """
        Call GET /api/v1/market-data/instruments/rates?instrumentIds=...

        eToro returns 500 when any single ID in the batch is invalid (e.g.
        virtual copy-trade instruments with unusual IDs).  When that happens
        this method retries each ID individually and silently skips any that
        still fail, mirroring the same fallback used in
        ``etoro_app.services.portfolio_service._fetch_market_data``.

        Returns a dict keyed by ``str(instrumentID)``.
        """
        url = f"{self._base_url}/api/v1/market-data/instruments/rates"

        def _parse(body) -> dict[str, dict]:
            raw_rates: list[dict] = (
                body.get("rates", []) if isinstance(body, dict) else []
            )
            return {
                str(r["instrumentID"]): r
                for r in raw_rates
                if "instrumentID" in r
            }

        # ── Batch attempt ─────────────────────────────────────────────────
        try:
            response = await client.get(
                url,
                headers=self._auth_headers(),
                params={"instrumentIds": ",".join(instrument_ids)},
                timeout=10,
            )
            if response.status_code != 500:
                response.raise_for_status()
                return _parse(response.json())
            # 500 → fall through to per-ID fallback below
            logger.warning(
                "eToro rates batch returned 500 — retrying %d IDs individually",
                len(instrument_ids),
            )
        except httpx.HTTPStatusError:
            raise
        except Exception:
            raise

        # ── Per-ID fallback ───────────────────────────────────────────────
        result: dict[str, dict] = {}
        for iid in instrument_ids:
            try:
                resp = await client.get(
                    url,
                    headers=self._auth_headers(),
                    params={"instrumentIds": iid},
                    timeout=10,
                )
                if resp.status_code == 500:
                    logger.debug("eToro rates: skipping invalid instrumentId=%s (500)", iid)
                    continue
                resp.raise_for_status()
                result.update(_parse(resp.json()))
            except httpx.HTTPStatusError as exc:
                logger.debug(
                    "eToro rates: skipping instrumentId=%s (%s)", iid, exc
                )
            except Exception as exc:
                logger.debug(
                    "eToro rates: error for instrumentId=%s: %s", iid, exc
                )
        return result

    async def stream(
        self,
        instrument_keys: list[str],
        name_map: dict[str, str] | None = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Infinite async generator that yields rate tick dicts every
        ``ETORO_POLL_INTERVAL`` seconds until the caller stops iterating.

        Args:
            instrument_keys: eToro instrumentId strings, e.g. ["100001", "1001"].
            name_map: Optional mapping of instrumentId string → display name,
                      e.g. {"100001": "Ethereum", "1001": "Apple"}.
                      When provided each tick entry includes a ``"name"`` field.
        """
        # Deduplicate while preserving order — eToro 500s when the same ID
        # appears twice in a batch (e.g. a symbol held in both a direct and
        # copy-trade position).
        seen: set[str] = set()
        unique_keys: list[str] = []
        for k in instrument_keys:
            if k not in seen:
                seen.add(k)
                unique_keys.append(k)

        _names: dict[str, str] = name_map or {}

        async with httpx.AsyncClient() as client:
            while True:
                ts = time.time()
                try:
                    raw = await self._fetch_rates(client, unique_keys)
                    ticks = {
                        iid: {
                            "name": _names.get(iid, iid),
                            "bid": info.get("bid"),
                            "ask": info.get("ask"),
                            "ts": ts,
                        }
                        for iid, info in raw.items()
                    }
                    yield {"broker": "etoro", "ticks": ticks, "ts": ts}
                except httpx.HTTPStatusError as exc:
                    status = exc.response.status_code
                    if status == 429:
                        retry_after = float(
                            exc.response.headers.get("Retry-After", _ETORO_429_DEFAULT_BACKOFF)
                        )
                        logger.warning(
                            "eToro rates 429 — pausing stream for %.0fs", retry_after
                        )
                        yield {"broker": "etoro", "error": f"Rate limited — retrying in {retry_after:.0f}s", "ts": ts}
                        await asyncio.sleep(retry_after)
                        continue  # skip the normal interval sleep below
                    logger.warning("eToro rates HTTP %s error: %s", status, exc)
                    yield {"broker": "etoro", "error": str(exc), "ts": ts}
                except Exception as exc:
                    logger.warning("eToro rates fetch error: %s", exc)
                    yield {"broker": "etoro", "error": str(exc), "ts": ts}
                await asyncio.sleep(ETORO_POLL_INTERVAL)
