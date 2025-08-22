from pydantic import BaseModel
from typing import List, Optional, Literal, Any, Dict

# ==== Command Messages ====
class Command(BaseModel):
    id: int
    cmd: Literal["subscribe", "unsubscribe", "update_subscription"]
    params: Dict[str, Any]

class SubscribeParams(BaseModel):
    channels: List[str]
    market_ticker: Optional[str] = None
    market_tickers: Optional[List[str]] = None

class SubscribeCommand(Command):
    cmd: Literal["subscribe"]
    params: SubscribeParams

class UnsubscribeParams(BaseModel):
    sids: List[int]

class UnsubscribeCommand(Command):
    cmd: Literal["unsubscribe"]
    params: UnsubscribeParams

class UpdateSubscriptionParams(BaseModel):
    sids: List[int]
    market_ticker: Optional[str] = None
    market_tickers: Optional[List[str]] = None
    action: Literal["add_markets", "delete_markets"]

class UpdateSubscriptionCommand(Command):
    cmd: Literal["update_subscription"]
    params: UpdateSubscriptionParams

# ==== Server -> Client Messages ====
class SubscribedMsgDetail(BaseModel):
    channel: str
    sid: int

class SubscribedMessage(BaseModel):
    id: int
    type: Literal["subscribed"]
    msg: SubscribedMsgDetail

class ErrorMsg(BaseModel):
    code: int
    msg: str

class ErrorMessage(BaseModel):
    id: Optional[int] = None
    type: Literal["error"]
    msg: ErrorMsg

class UnsubscribedMessage(BaseModel):
    sid: int
    type: Literal["unsubscribed"]

class OkMessage(BaseModel):
    id: int
    sid: int
    seq: int
    type: Literal["ok"]
    market_tickers: List[str]

# --- Orderbook channel ---
class OrderbookSnapshotDetail(BaseModel):
    market_ticker: str
    yes: Optional[List[List[int]]] = None
    no: Optional[List[List[int]]] = None

class OrderbookSnapshotMessage(BaseModel):
    type: Literal["orderbook_snapshot"]
    sid: int
    seq: int
    msg: OrderbookSnapshotDetail

class OrderbookDeltaDetail(BaseModel):
    market_ticker: str
    price: int
    delta: int
    side: Literal["yes", "no"]

class OrderbookDeltaMessage(BaseModel):
    type: Literal["orderbook_delta"]
    sid: int
    seq: int
    msg: OrderbookDeltaDetail

# --- Ticker channels ---
class TickerDetail(BaseModel):
    market_ticker: str
    price: int
    yes_bid: int
    yes_ask: int
    volume: int
    open_interest: int
    dollar_volume: int
    dollar_open_interest: int
    ts: int

class TickerMessage(BaseModel):
    type: Literal["ticker"]
    sid: int
    msg: TickerDetail

class TickerV2Detail(BaseModel):
    market_ticker: str
    price: Optional[int] = None
    yes_bid: Optional[int] = None
    yes_ask: Optional[int] = None
    no_bid: Optional[int] = None
    no_ask: Optional[int] = None
    volume_delta: Optional[int] = None
    open_interest_delta: Optional[int] = None
    dollar_volume_delta: Optional[int] = None
    dollar_open_interest_delta: Optional[int] = None
    ts: int

class TickerV2Message(BaseModel):
    type: Literal["ticker_v2"]
    sid: int
    msg: TickerV2Detail

# --- Trade channel ---
class TradeDetail(BaseModel):
    market_ticker: str
    yes_price: int
    no_price: int
    count: int
    taker_side: Literal["yes", "no"]
    ts: int

class TradeMessage(BaseModel):
    type: Literal["trade"]
    sid: int
    msg: TradeDetail

# --- Fill channel ---
class FillDetail(BaseModel):
    trade_id: str
    order_id: str
    market_ticker: str
    is_taker: bool
    side: Literal["yes", "no"]
    yes_price: int
    no_price: int
    count: int
    action: Literal["buy", "sell"]
    ts: int

class FillMessage(BaseModel):
    type: Literal["fill"]
    sid: int
    msg: FillDetail

# --- Market Lifecycle V2 channel ---
class MarketLifecycleV2Detail(BaseModel):
    event_type: str
    market_ticker: str
    open_ts: Optional[int] = None
    close_ts: Optional[int] = None
    result: Optional[str] = None
    determination_ts: Optional[int] = None
    settled_ts: Optional[int] = None
    is_deactivated: Optional[bool] = None
    additional_metadata: Optional[Dict[str, Any]] = None

class MarketLifecycleV2Message(BaseModel):
    type: Literal["market_lifecycle_v2"]
    sid: int
    msg: MarketLifecycleV2Detail

# --- Event Lifecycle channel ---
class EventLifecycleDetail(BaseModel):
    event_ticker: str
    title: str
    sub_title: str
    collateral_return_type: str
    series_ticker: str
    strike_date: Optional[int] = None
    strike_period: Optional[str] = None

class EventLifecycleMessage(BaseModel):
    type: Literal["event_lifecycle"]
    sid: int
    msg: EventLifecycleDetail

# --- Deprecated Market Lifecycle channel ---
class MarketLifecycleDetail(BaseModel):
    market_ticker: str
    open_ts: int
    close_ts: int
    determination_ts: Optional[int] = None
    settled_ts: Optional[int] = None
    result: Optional[str] = None
    is_deactivated: Optional[bool] = None
    additional_metadata: Optional[Dict[str, Any]] = None

class MarketLifecycleMessage(BaseModel):
    type: Literal["market_lifecycle"]
    sid: int
    msg: MarketLifecycleDetail

# --- Multivariate channel ---
class SelectedMarket(BaseModel):
    event_ticker: str
    market_ticker: str
    side: str

class MultivariateLookupDetail(BaseModel):
    collection_ticker: str
    event_ticker: str
    market_ticker: str
    selected_markets: List[SelectedMarket]

class MultivariateLookupMessage(BaseModel):
    type: Literal["multivariate_lookup"]
    sid: int
    msg: MultivariateLookupDetail
