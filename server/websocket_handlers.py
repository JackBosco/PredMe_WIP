import asyncio
import json
import websockets as ws
from typing import Any, Coroutine, List

from polymarket_client import PolymarketWebSocketClient
import polymarket_wss_dtypes as ptypes
from server_internal_dtypes import Auth_Kalshi, Endpoint, LOB_Entry, OrderBook_Key
from kalshi_client import KalshiWebSocketClient
from kalshi_tickerv2_dtypes import OrderbookDeltaMessage, OrderbookSnapshotMessage, SubscribedMessage, TickerV2Message
from orderbook_ext import ServerState, LOBEntry as _LOBEntry

def _lob(price: float, quantity: float) -> _LOBEntry:
    return _LOBEntry(price, quantity)

async def spawn_extern_listener(endpoints: List[Endpoint], auths: List[Any] = [], verbose=False):
    """
    Start the external endpoint listener, which spawns new threads
    for each endpoint and updates the list of threads externs
    """
    polymarket_markets = []
    kalshi_markets = []
    for ep in endpoints:
        if ep.exchange_id == 'polymarket':
            polymarket_markets.append(ep)
        elif ep.exchange_id == 'kalshi':
            kalshi_markets.append(ep)
    tasks = []
    if polymarket_markets:
        tasks.append(asyncio.create_task(polymarket_ws_handler(polymarket_markets, verbose=verbose)))
    if kalshi_markets:
        try:
            auth_kalshi = [ah for ah in auths if isinstance(ah, Auth_Kalshi)][0]
        except Exception as e:
            raise Exception(f"Needed kalshi private key, got {auths}")
        tasks.append(asyncio.create_task(kalshi_ws_handler(kalshi_markets, auth=auth_kalshi, verbose=verbose)))
    await asyncio.gather(*tasks)

def _update_serverstate_from_polymarket(state: ServerState, msg: ws.Data):
    __m_ = json.loads(msg)
    for __m in __m_:
        match __m["event_type"]:
            case "book":
                _m = ptypes.BookMessage(**__m)
                key_exchange = 'polymarket'
                bids = [_lob(b.price, b.size) for b in _m.bids]
                offers = [_lob(o.price, o.size) for o in _m.asks]
                state.init_order_book(key_exchange, _m.asset_id, bids, offers)
            case "price_change":
                _m = ptypes.PriceChangeMessage(**__m)
                token_id = _m.asset_id
                bid_updates = []
                offer_updates = []
                for change in _m.changes:
                    if change.side == 'BUY':
                        bid_updates.append(_lob(change.price, change.size))
                    else:
                        offer_updates.append(_lob(change.price, change.size))
                if bid_updates:
                    state.update_order_book('polymarket', token_id, 'y', 'b', bid_updates, False)
                if offer_updates:
                    state.update_order_book('polymarket', token_id, 'y', 'o', offer_updates, False)
            case "tick_size_change":
                _m = ptypes.TickSizeChangeMessage(**__m)
                state.set_tick_size('polymarket', _m.asset_id, _m.new_tick_size)
            case "last_trade_price":
                pass
            case _:
                raise Exception("got unrecognized type from message", msg)

async def polymarket_ws_handler(market_tickers: List[Endpoint], verbose=False):
    state: ServerState = ServerState() # type: ignore

    client = PolymarketWebSocketClient(
        asset_ids=[m.market_id for m in market_tickers if m.exchange_id=='polymarket'],
        channel='market',
        on_message=lambda _, msg: _update_serverstate_from_polymarket(state, msg),
    )

    await client.connect()

def _update_serverstate_from_kalshi(state: ServerState, msg: ws.Data):
    __m = json.loads(msg)
    match __m['type']:
        case "ticker_v2":
            _m = TickerV2Message(**__m)
        case "subscribed":
            _m = SubscribedMessage(**__m)
        case "orderbook_snapshot":
            _m = OrderbookSnapshotMessage(**__m)
            bids = []
            offers = []
            if _m.msg.yes:
                bids = [_lob(round(d[0] / 100, 3), d[1]) for d in _m.msg.yes]
            if _m.msg.no:
                offers = [_lob(round(1 - (d[0] / 100), 3), d[1]) for d in _m.msg.no]
            state.init_order_book('kalshi', _m.msg.market_ticker, bids, offers)
        case "orderbook_delta":
            _m = OrderbookDeltaMessage(**__m)
            pred = 'y' if _m.msg.side == "yes" else 'n'
            state.update_order_book('kalshi', _m.msg.market_ticker, pred, 'b', _lob(_m.msg.price / 100, _m.msg.delta), True)

async def kalshi_ws_handler(market_tickers: List[Endpoint], auth: Auth_Kalshi, verbose=False):
    state: ServerState = ServerState() # type: ignore

    ws_client = KalshiWebSocketClient(
        key_id=auth.keyid,
        private_key=auth.private_key, # type: ignore
        environment=auth.env,
        on_message_callback = lambda _, msg: _update_serverstate_from_kalshi(state, msg),
        tickers=[m.market_id for m in market_tickers if m.exchange_id=='kalshi'],
    )

    await ws_client.connect()
    await ws_client.handler()