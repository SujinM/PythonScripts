"""
app/api/v1/live.py
──────────────────
WebSocket endpoint for live price streaming.

  WS  /api/v1/{broker}/ws/live?instruments=KEY1,KEY2,...

The client connects and immediately starts receiving JSON price-tick messages.

If the ``instruments`` query parameter is omitted the server auto-resolves
the broker's current holdings and streams those instrument keys.

Supported brokers
─────────────────
  upstox  — polls GET /v2/market-quote/ltp every 1 s
              → ticks keyed by instrument_key ("NSE_EQ|INE848E01016")
  etoro   — connects to wss://ws.etoro.com/ws (native WebSocket)
              server PUSHES on every price change (sub-second latency, no polling)
              → ticks keyed by str(instrumentId) ("100001")

Example connections
───────────────────
  # Auto-resolve holdings:
  ws://localhost:8000/api/v1/upstox/ws/live
  ws://localhost:8000/api/v1/etoro/ws/live

  # Explicit instruments (URL-encode the pipe character):
  ws://localhost:8000/api/v1/upstox/ws/live?instruments=NSE_EQ%7CINE848E01016
  ws://localhost:8000/api/v1/etoro/ws/live?instruments=100001,1001

Pushed message format
─────────────────────
  Upstox success:
    {
      "broker": "upstox",
      "ticks": {
        "NSE_EQ|INE848E01016": {"ltp": 1234.5, "close": 1230.0, "ts": 1746567890.1}
      },
      "ts": 1746567890.1
    }

  eToro success (pushed on every price change — sub-second):
    {
      "broker": "etoro",
      "ticks": {
        "100001": {"name": "Ethereum", "bid": 1234.5, "ask": 1235.0, "ts": 1746567890.1}
      },
      "ts": 1746567890.1
    }

  Error / reconnect frame:
    {"broker": "etoro", "error": "Disconnected — reconnecting in 3s", "ts": 1746567890.1}

WebSocket close codes
─────────────────────
  4004 — broker not supported or not found in registry
  4000 — no instrument keys could be resolved
  4011 — unexpected server-side error
"""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from app.api.deps import get_portfolio_service
from app.core.exceptions import BrokerNotFoundError
from app.core.logger import get_logger
from app.services.live_service import EToroLiveService, UpstoxLiveService
from app.services.portfolio_service import PortfolioService

router = APIRouter(tags=["live"])
logger = get_logger(__name__)

# Map broker_id → live service class
_LIVE_SERVICES = {
    "upstox": UpstoxLiveService,
    "etoro": EToroLiveService,
}


@router.websocket("/{broker}/ws/live")
async def live_prices(
    websocket: WebSocket,
    broker: str,
    instruments: Annotated[
        str,
        Query(
            description=(
                "Comma-separated instrument keys to stream. "
                "Omit to auto-resolve from the broker's current holdings."
            )
        ),
    ] = "",
    svc: PortfolioService = Depends(get_portfolio_service),
) -> None:
    """
    Stream live LTP / bid-ask ticks for the given broker via WebSocket.

    Connect from Python::

        import asyncio, websockets, json

        async def main():
            uri = "ws://localhost:8000/api/v1/upstox/ws/live"
            async with websockets.connect(uri) as ws:
                async for msg in ws:
                    print(json.loads(msg))

        asyncio.run(main())

    Connect from JavaScript::

        const ws = new WebSocket("ws://localhost:8000/api/v1/upstox/ws/live");
        ws.onmessage = (e) => console.log(JSON.parse(e.data));
    """
    # ── Validate broker ───────────────────────────────────────────────────
    service_cls = _LIVE_SERVICES.get(broker)
    if service_cls is None:
        await websocket.close(
            code=4004,
            reason=f"Broker '{broker}' is not supported for live feed. "
            f"Supported: {', '.join(_LIVE_SERVICES)}",
        )
        return

    await websocket.accept()
    logger.info(
        "Live WS connected: broker=%s client=%s instruments=%r",
        broker,
        websocket.client,
        instruments or "<auto>",
    )

    # ── Resolve instrument keys (and names for eToro) ─────────────────────
    name_map: dict[str, str] = {}
    if instruments:
        keys = [k.strip() for k in instruments.split(",") if k.strip()]
    else:
        # Auto-derive instrument keys from the broker's current holdings.
        # For eToro, also build a name_map so the dashboard can show symbols.
        try:
            holdings = svc.get_holdings(broker)
            keys = [h.instrument_key for h in holdings]
            if broker == "etoro":
                name_map = {
                    h.instrument_key: h.trading_symbol
                    for h in holdings
                    if h.trading_symbol
                }
        except BrokerNotFoundError:
            await websocket.close(
                code=4004,
                reason=f"Broker '{broker}' not found in registry",
            )
            return
        except Exception as exc:
            logger.warning(
                "Cannot auto-resolve holdings for %s: %s", broker, exc
            )
            keys = []

    if not keys:
        await websocket.send_text(
            json.dumps({"error": "No instrument keys to stream", "broker": broker})
        )
        await websocket.close(code=4000, reason="No instrument keys resolved")
        return

    logger.info("Streaming %d instrument(s) for broker=%s", len(keys), broker)

    # ── Stream ticks until client disconnects ─────────────────────────────
    live_svc = service_cls()
    try:
        # EToroLiveService.stream() accepts an optional name_map;
        # UpstoxLiveService.stream() does not — pass it only for eToro.
        stream_kwargs: dict = {"name_map": name_map} if broker == "etoro" else {}
        async for tick in live_svc.stream(keys, **stream_kwargs):
            await websocket.send_text(json.dumps(tick))
    except WebSocketDisconnect:
        logger.info("Live WS disconnected: broker=%s", broker)
    except Exception as exc:
        logger.error("Live WS server error for broker=%s: %s", broker, exc)
        try:
            await websocket.close(code=4011, reason="Server error")
        except Exception:
            pass
