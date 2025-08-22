#server/ServerState.py
import asyncio
from collections.abc import Hashable
import math
from typing import Dict, List, Tuple, Literal
from pydantic import BaseModel
from OrderBook import OrderBook

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

class OrderBook_Key(BaseModel, Hashable):
    """
    exchange_id: str
    market_id:   str
    """
    exchange_id: str
    market_id:   str

    class Config:
        frozen=True


class ServerState(object):
    """Singleton server state managing market data with asyncio concurrency."""

    _instance = None
    _order_books: Dict[OrderBook_Key, OrderBook]
    _locks: Dict[OrderBook_Key, asyncio.Lock]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._locks = {}
            cls._instance._order_books= {}
        return cls._instance

    async def update_order_book(self, exchange_id: str, market_id: str, pred: Literal["y" , "n"], side: Literal["b", "o"], data: LOB_Entry | List[LOB_Entry], is_delta: bool=False):
        """
        Update the order book held by internal server state.
        Locks on order book.
        The price to buy a "yes" ticket is the bid price, the price to sell a "yes" ticket == 1 - the price to buy a "no" ticket == the offer price

        internally everything is converted to the "yes" perspective

        Each entry should be of the form
        {
            "price": float,
            "quantity": int
        }
        """
        match pred, side:
            case 'y', _:
                _side = side
            case 'n', 'b':
                _side = 'o'
                if isinstance(data, list):
                    for i in range(len(data)):
                        data[i].price = 1 - data[i].price
                else:
                    data.price = 1 - data.price
            case 'n', 'o':
                _side = 'b'

        key = OrderBook_Key(exchange_id=exchange_id, market_id=market_id)
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        async with self._locks[key]:
            if isinstance(data, list):
                await self._order_books[key].update_levels(entries=data, side=_side, is_delta=is_delta)
            else:
                await self._order_books[key].update_level(entry=data, side=_side, is_delta=is_delta)

    async def get_market(self, exchange_id: str, market_id: str, pred: Literal["y", "n"], side: Literal["b", "o"]) -> Tuple[List[LOB_Entry], List[LOB_Entry]]:
        """
        Wait for the lock and get the entire order book from the exchange.

        Returns:
            b : list of open bids
            o : list of open offers
        """
        key = OrderBook_Key(exchange_id=exchange_id, market_id=market_id)
        # TODO use a read lock instead of a mutex
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        async with self._locks[key]:
            book = self._order_books[key]
            t = book._tick_size
            b = list([LOB_Entry(quantity=q, price=p * t) for p, q in enumerate(book._bids) if q != 0])
            o = list([LOB_Entry(quantity=q, price=p * t) for p, q in enumerate(book._offers) if q != 0])
            return b, o

    async def init_order_book(self, key: OrderBook_Key, bids: List[LOB_Entry], offers: List[LOB_Entry]):

        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
            async with self._locks[key]:
                self._order_books[key] = OrderBook(key, bids, offers)
        elif key in self._order_books.keys():
            # already initialized
            await asyncio.gather(
                self.update_order_book(side='b', data=bids, exchange_id=key.exchange_id, market_id=key.market_id, pred='y'),
                self.update_order_book(side='o', data=offers, exchange_id=key.exchange_id, market_id=key.market_id, pred='y')
            )
    def _fmt_size(self, s: float, sp:str =' ')->str:
        return f"{s:{sp}>12.2f}" if s %1 != 0.0 else f"{s:{sp}>9.0f}." + sp * 2

    def get_lobs(self, lob_depth, col_width=25):
        cols = []
        for mar in self._order_books.values():
            col, mid = mar.get_col()
            mnum = self._fmt_size(col[math.floor(mid)+1][1], sp='-')
            if mid % 1.0 != 0.0:
                mnum = f"{'+':-^12}"
            col_fmt = [f'{f"{col[math.floor(mid)+1][0]:-<4}, {mnum}":-^25}']
            for i in range(1, lob_depth+1):
                b = min(len(col)-1, math.floor(mid) + i+1)
                u = max(0, math.ceil(mid) - i)
                col_fmt = [f"{col[u][0]:<4}, {self._fmt_size(col[u][1])}"] + col_fmt + [f"{col[b][0]:<4}, {self._fmt_size(col[b][1])}"]
            cols.append([f"[{s:^{col_width}}]" for s in col_fmt])
        return cols

    def __repr__(self):
        LOB_DEPTH=5
        cols = self.get_lobs(LOB_DEPTH, col_width=25)
        ret = []
        for row in range(LOB_DEPTH*2-1, 0, -1):
            _r = []
            for col in cols:
                _r.append(col[row])
            ret.append(''.join(_r))
        return '\n'.join(ret)