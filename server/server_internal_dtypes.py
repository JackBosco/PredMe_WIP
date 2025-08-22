from collections.abc import Hashable
from typing import Any, Optional
from pydantic import BaseModel
from kalshi_client import Environment as KEnv


class Endpoint(BaseModel):
    """
    exchange_id : polymarket or kalshi
    market_id   : the hash or token pointing to a market on the exchange
    market_name : the name of the market or event, which is predicted
    token_ids   : the hash or token pointing to a prediction [y, n]
    direction   : the literal for the prediction [y, n]
    group_id    : if there is a pair of markets that are essentially the same
                  across multiple exchanges, use this to categorize that
    desctiption : other info
    """
    exchange_id: str
    market_id:   str
    market_name: Optional[str]
    token_id:    Optional[str]
    group_id   : Optional[int]
    description: Optional[str]

class OrderBook_Key(BaseModel, Hashable):
    """
    exchange_id: str
    market_id:   str
    """
    exchange_id: str
    market_id:   str

    class Config:
        frozen=True

class Market_Group(BaseModel):
    """
    _id        : int
    markets    : list[tuple[str, str]]
    """
    _id        : int
    markets    : list[tuple[str, str]]

class Auth_Kalshi(BaseModel):
    keyid      : str
    env        : KEnv
    private_key: Any

class Auth_Polymarket(BaseModel):
    # TODO
    # not necessary for data stream
    pass

class Trade(BaseModel):
    """
    created when a buy and sell order get matched
    """
    price       : float
    quantity    : float

class LOB_Entry(BaseModel):
    """
    price      : float
    quantity   : int
    """
    price      : float
    quantity   : float