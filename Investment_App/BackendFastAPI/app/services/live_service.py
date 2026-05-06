"""
app/services/live_service.py
─────────────────────────────
Live price streaming services for Upstox and eToro.

Architecture
────────────
  Client ←── FastAPI WebSocket ─── LiveService ─── Broker data source

Upstox
  Source  : GET /v2/market-quote/ltp (REST poll every 1 s)
  Keys    : Upstox instrument keys, e.g. "NSE_EQ|INE848E01016"

eToro
  Source  : wss://ws.etoro.com/ws  (native WebSocket — push on every price change)
  Keys    : str(instrumentId), e.g. "100001"
  Protocol:
    1. Connect to wss://ws.etoro.com/ws
    2. Send Authenticate  {"operation": "Authenticate", "data": {"userKey": ..., "apiKey": ...}}
    3. Receive            {"success": true, "operation": "Authenticate"}
    4. Send Subscribe     {"operation": "Subscribe", "data": {"topics": ["instrument:100001", ...], "snapshot": true}}
    5. Receive push msgs  {"messages": [{"topic": "instrument:100001", "content": "{\"Bid\":\"...\",\"Ask\":\"...\"}", "type": "Trading.Instrument.Rate"}]}
    6. On disconnect → reconnect automatically
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import AsyncGenerator

import httpx
import websockets

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)

UPSTOX_POLL_INTERVAL: float = 1.0   # seconds between Upstox LTP polls


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
    Streams live bid/ask rates from eToro using the **native WebSocket API**
    at ``wss://ws.etoro.com/ws``.

    Unlike the previous REST-polling approach, the eToro server *pushes* a
    new message on every price change — no polling interval, no 429 errors,
    and sub-second latency.

    Protocol (per eToro API docs):
      1. Connect  →  wss://ws.etoro.com/ws
      2. Authenticate  →  ``{"operation": "Authenticate", "data": {"userKey": ..., "apiKey": ...}}``
      3. Subscribe     →  ``{"operation": "Subscribe", "data": {"topics": ["instrument:100001", ...], "snapshot": true}}``
      4. Receive push  →  ``{"messages": [{"topic": "instrument:100001", "content": "{...}", "type": "Trading.Instrument.Rate"}]}``
         The ``content`` field is a JSON string with keys ``Bid``, ``Ask``, ``LastExecution``, ``Date``.
      5. On disconnect → auto-reconnect with a short delay.

    Yielded message shape (success)::

        {
          "broker": "etoro",
          "ticks": {
            "100001": {"name": "Ethereum", "bid": 1234.5, "ask": 1235.0, "ts": 1746567890.1},
            ...
          },
          "ts": 1746567890.1
        }

    Yielded message shape (error / reconnect)::

        {"broker": "etoro", "error": "...", "ts": 1746567890.1}
    """

    _WS_URL = "wss://ws.etoro.com/ws"
    _RECONNECT_DELAY: float = 3.0   # seconds before reconnect attempt
    _AUTH_TIMEOUT: float = 15.0     # seconds to wait for auth response

    def __init__(self) -> None:
        s = get_settings()
        self._api_key = s.etoro_api_key
        self._user_key = s.etoro_user_key

    @staticmethod
    def _decode_frame(raw) -> dict | None:
        """
        Decode a WebSocket frame to a dict.

        The eToro server may send binary frames, empty frames, or plain-text
        non-JSON frames (e.g. a ping/keep-alive byte).  Return ``None`` for
        anything that is not a parseable JSON object so callers can skip it.
        """
        if not raw:
            return None
        if isinstance(raw, (bytes, bytearray)):
            try:
                raw = raw.decode("utf-8")
            except UnicodeDecodeError:
                return None
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            logger.debug("eToro WS: skipping non-JSON frame: %r", raw[:120])
            return None

    async def stream(
        self,
        instrument_keys: list[str],
        name_map: dict[str, str] | None = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Infinite async generator that yields bid/ask tick dicts pushed by the
        eToro WebSocket server on every price change.

        Args:
            instrument_keys: eToro instrumentId strings, e.g. ["100001", "1001"].
            name_map: Optional mapping of instrumentId string → display name.
                      Each tick entry includes a ``"name"`` field; falls back
                      to the numeric ID string when not provided.
        """
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_keys: list[str] = []
        for k in instrument_keys:
            if k not in seen:
                seen.add(k)
                unique_keys.append(k)

        if not unique_keys:
            yield {"broker": "etoro", "error": "No instrument keys provided", "ts": time.time()}
            return

        _names: dict[str, str] = name_map or {}
        topics = [f"instrument:{iid}" for iid in unique_keys]

        while True:
            ts = time.time()
            try:
                async with websockets.connect(self._WS_URL) as ws:
                    logger.info(
                        "eToro WS connected — authenticating (%d instruments)", len(unique_keys)
                    )

                    # ── Step 1: Authenticate ──────────────────────────────
                    await ws.send(json.dumps({
                        "id": str(uuid.uuid4()),
                        "operation": "Authenticate",
                        "data": {
                            "userKey": self._user_key,
                            "apiKey": self._api_key,
                        },
                    }))

                    # Wait for the auth response — skip empty / non-JSON frames
                    # (the server may send a ping or binary handshake frame first).
                    auth_resp: dict | None = None
                    deadline = asyncio.get_event_loop().time() + self._AUTH_TIMEOUT
                    while auth_resp is None:
                        remaining = deadline - asyncio.get_event_loop().time()
                        if remaining <= 0:
                            raise TimeoutError("Timed out waiting for eToro auth response")
                        raw_auth = await asyncio.wait_for(ws.recv(), timeout=remaining)
                        auth_resp = self._decode_frame(raw_auth)

                    if not auth_resp.get("success", False):
                        err = auth_resp.get("errorMessage") or auth_resp.get("errorCode", "unknown")
                        logger.error("eToro WS authentication failed: %s", err)
                        yield {
                            "broker": "etoro",
                            "error": f"Authentication failed: {err}",
                            "ts": time.time(),
                        }
                        await asyncio.sleep(self._RECONNECT_DELAY)
                        continue

                    logger.info(
                        "eToro WS authenticated — subscribing to %d topic(s)", len(topics)
                    )

                    # ── Step 2: Subscribe (snapshot=True → get prices now) ─
                    await ws.send(json.dumps({
                        "id": str(uuid.uuid4()),
                        "operation": "Subscribe",
                        "data": {
                            "topics": topics,
                            "snapshot": True,
                        },
                    }))

                    # ── Step 3: Process incoming push messages ─────────────
                    async for raw in ws:
                        ts = time.time()
                        msg = self._decode_frame(raw)
                        if msg is None:
                            continue  # skip empty / binary / non-JSON frames
                        try:
                            messages: list[dict] = msg.get("messages", [])
                            ticks: dict[str, dict] = {}

                            for m in messages:
                                topic: str = m.get("topic", "")
                                if not topic.startswith("instrument:"):
                                    continue  # e.g. subscription ack / private messages
                                iid = topic.split(":", 1)[1]

                                # content is a nested JSON string
                                content_raw = m.get("content", "{}")
                                content: dict = (
                                    json.loads(content_raw)
                                    if isinstance(content_raw, str)
                                    else content_raw
                                )

                                bid = float(content["Bid"]) if "Bid" in content else None
                                ask = float(content["Ask"]) if "Ask" in content else None

                                ticks[iid] = {
                                    "name": _names.get(iid, iid),
                                    "bid": bid,
                                    "ask": ask,
                                    "ts": ts,
                                }

                            if ticks:
                                yield {"broker": "etoro", "ticks": ticks, "ts": ts}

                        except Exception as exc:
                            logger.warning("eToro WS message parse error: %s", exc)

            except asyncio.CancelledError:
                raise  # propagate cancellation to the caller
            except Exception as exc:
                ts = time.time()
                logger.warning(
                    "eToro WS error: %s — reconnecting in %.0fs", exc, self._RECONNECT_DELAY
                )
                yield {
                    "broker": "etoro",
                    "error": f"Disconnected — reconnecting in {self._RECONNECT_DELAY:.0f}s",
                    "ts": ts,
                }
                await asyncio.sleep(self._RECONNECT_DELAY)

