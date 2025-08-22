import asyncio
import websockets
from pydantic import BaseModel
from typing import Any, Coroutine, List, Literal, Optional, Callable, Awaitable, Union
from polymarket_wss_dtypes import SubscribeMessage, Auth

class PolymarketWebSocketClient:
    """Client for Polymarket CLOB WebSocket (USER or MARKET channels)."""

    WSS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/"
    # WSS_URL = "wss://ws-live-data.polymarket.com/"

    def __init__(
        self,
        apikey: Optional[str] = None,
        secret: Optional[str] = None,
        passphrase: Optional[str] = None,
        channel: Literal["user", "market"] = 'market',
        markets: Optional[List[str]] = None,
        asset_ids: Optional[List[str]] = None,
        on_message: Union[Callable[[Any, str], Awaitable], Callable[[Any, str], None]] = lambda msg: None, # type: ignore
        on_error: Callable[[Exception], None] = lambda err: None,
        on_close: Callable[[int, str], None] = lambda code, reason: None,
        on_open: Callable[[], None] = lambda: None,
    ):
        """
        - apikey/secret/(passphrase):
        - channel: 'USER' or 'MARKET' subscription type
        - markets: list of market IDs (required if channel=='USER')
        - asset_ids: list of asset IDs (required if channel=='MARKET')
        - callback hooks for messages, errors, close, and open.
        """
        if all((apikey, secret, passphrase)):
            self.auth = Auth(apikey=apikey, secret=secret, passphrase=passphrase)
        else:
            self.auth = None
        self.channel = channel
        self.markets = markets
        self.asset_ids = asset_ids
        self.on_message = on_message
        self.on_error = on_error
        self.on_close = on_close
        self.on_open = on_open

    async def connect(self) -> None:
        """Open WebSocket, perform subscription, and start message loop."""
        try:
            async with websockets.connect(
                uri=self.WSS_URL + self.channel.lower(),
                ping_interval=30, ping_timeout=10,
                origin='https://polymarket.com' # type: ignore
            ) as ws:
                self.ws = ws
                await self._send_subscribe()
                self.on_open()
                await self._receive_loop()
        except Exception as e:
            self._on_error(e)
            raise e

    async def _send_subscribe(self) -> None:
        """Builds and sends the SubscribeMessage per Polymarket spec."""
        sub = SubscribeMessage(
            auth=self.auth, # type: ignore
            type='MARKET' if self.channel.lower()=='market' else 'USER', # type: ignore
            markets=self.markets,
            assets_ids=self.asset_ids
        )
        # Use by_alias to emit "type" and "hash" exactly as in docs:contentReference[oaicite:8]{index=8}
        sub_msg=sub.model_dump_json(exclude_none=True)
        print(sub_msg)
        await self.ws.send(sub_msg)

    async def _receive_loop(self) -> None:
        """Continuously read from WS and dispatch messages or handle close."""
        async for raw in self.ws:
            await self._on_message(raw)
        # except websockets.connectionclosed as e:
        #     self.on_close(e.code, e.reason)
        # except Exception as e:
        #     self.on_error(e)

    async def _on_message(self, msg: websockets.Data):
        res = self.on_message(self, msg) # type: ignore
        if isinstance(res, Coroutine):
            await res

    def _on_error(self, e):
        raise e