from pydantic import BaseModel, Field
from typing import Any, List, Literal, Optional
from decimal import Decimal

# === Subscription Message ===
class Auth(BaseModel):
    apikey: Optional[str]
    secret: Optional[str]
    passphrase: Optional[str] = None

class SubscribeMessage(BaseModel):
    auth: Auth | None
    type: Any#Literal["USER", "MARKET"]
    markets: Optional[List[str]] = None
    assets_ids: Optional[List[str]] = None


# === Market Data Messages ===
class OrderSummary(BaseModel):
    price: float
    size: float

class BookMessage(BaseModel):
    event_type: Literal["book"] = Field(..., alias="event_type")
    asset_id: str
    market: str
    bids: List[OrderSummary]
    asks: List[OrderSummary]
    timestamp: int
    hash_value: str = Field(..., alias="hash")

class ChangeDetail(BaseModel):
    price: float
    side: Literal["BUY", "SELL"]
    size: float

class PriceChangeMessage(BaseModel):
    event_type: Literal["price_change"] = Field(..., alias="event_type")
    asset_id: str
    changes: List[ChangeDetail]
    market: str
    timestamp: int
    hash_value: str = Field(..., alias="hash")

class TickSizeChangeMessage(BaseModel):
    event_type: Literal["tick_size_change"] = Field(..., alias="event_type")
    asset_id: str
    market: str
    old_tick_size: Decimal
    new_tick_size: Decimal
    timestamp: int

class LastTradePriceMessage(BaseModel):
    event_type: Literal["last_trade_price"] = Field(..., alias="event_type")
    asset_id: str
    fee_rate_bps: Decimal
    market: str
    price: Decimal
    side: Literal["BUY", "SELL"]
    size: Decimal
    timestamp: int
