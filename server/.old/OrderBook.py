#server/OrderBook.py
import asyncio
from collections.abc import Hashable
import math
from typing import Dict, List, Tuple, Literal
from pydantic import BaseModel

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


class OrderBook:

    _bids: List[float]
    _offers: List[float]

    def __init__(self, key: OrderBook_Key, bids: List[LOB_Entry], offers: List[LOB_Entry], tick_size: float = 0.01):
        self._key = key
        self._bids = [0] * (int(1 / tick_size) + 1)
        for b in bids:
            self._bids[round(b.price / tick_size)] = b.quantity
        self._offers = [0] * (int(1 / tick_size) + 1)
        for o in offers:
            self._offers[round(o.price / tick_size)] = o.quantity
        self._tick_size = tick_size

    def set_tick_size(self, tick_size):
        """ updates data structure to safely set tick size """
        if self._tick_size == tick_size:
            return

        conv: float = self._tick_size / tick_size
        new_bids: List[float] = [0] * (int(1 / tick_size) + 1)
        for i in range(len(self._bids)):
            new_bids[math.floor(i * conv)] += self._bids[i]
        new_offers: List[float] = [0] * (int(1 / tick_size) + 1)
        for i in range(len(self._offers)):
            new_offers[math.ceil(i * conv)] += self._offers[i]
        self._tick_size = tick_size


    def get_best(self) -> Tuple[LOB_Entry | None, LOB_Entry | None]:
        """
        Gets and returns the best bid and offer, or None if there are no bids or asks listed
        """
        bi = max([i[0] for i in enumerate(self._bids) if i[1] != 0] + [0])
        oi = min([i[0] for i in enumerate(self._offers) if i[1] != 0] + [100])
        b = None if bi==0 else LOB_Entry(price=bi * self._tick_size, quantity=self._bids[bi])
        o = None if oi==100 else LOB_Entry(price=oi * self._tick_size, quantity=self._offers[oi])
        return (b, o)

    async def update_level(self, entry: LOB_Entry, side: Literal['b', 'o'], is_delta=False):
        """ updates the order book directly without executing any trades """
        i = round(entry.price / self._tick_size)
        if side == 'b':
            cur: float = self._bids[i]
            self._bids[i] = cur + entry.quantity if is_delta else entry.quantity
        if side == 'o':
            cur: float = self._offers[i]
            self._offers[i] = cur + entry.quantity if is_delta else entry.quantity

    async def update_levels(self, entries: List[LOB_Entry], side: Literal['b', 'o'], is_delta=False):
        """ updates the order book directly multiple times without executing any trades """
        if side == 'b':
            for entry in entries:
                i = round(entry.price / self._tick_size)
                cur: float = self._bids[i]
                self._bids[i] = cur + entry.quantity if is_delta else entry.quantity
        else:
            for entry in entries:
                i = round(entry.price / self._tick_size)
                cur: float = self._offers[i]
                self._offers[i] = cur + entry.quantity if is_delta else entry.quantity


    async def add_limit_order(self, entry: LOB_Entry, side: Literal['b','o']) -> List[Trade]:
        """
        Updates the order book with a singular bid or offer order update.
        If the update results in crossing orders, match orders and generate
        corresponding Trade objects.
        We use the midpoint price as the trade price (could also use offer-price, weighted avg, etc.)


        Args:
            entry (LOB_Entry_Update): The incoming order book update entry.

        Returns:
            List[Trade]: A list of Trade objects for any matched orders.
        """
        trades: List[Trade] = []
        order_q = entry.quantity
        p = int(entry.price / self._tick_size)
        fully_ex = False


        # ===== BIDS =====
        if side == 'b':
            i = 0
            while i < len(self._offers) and i <= p:
                vol = min(order_q, self._offers[i])
                if vol > 0:
                    trades.append(Trade(quantity=vol, price=i*self._tick_size))
                    self._offers[i] -= vol
                    order_q -= vol
                elif order_q == 0:
                    fully_ex = True
                    break
                i += 1

            if not fully_ex:
                self._bids[p] += order_q

        # ===== OFFERS ======
        else:
            i = 100
            while i >= 0 and i >= p:
                vol = min(order_q, self._bids[i])
                if vol > 0:
                    trades.append(Trade(quantity=vol, price=i*self._tick_size))
                    self._bids[i] -= vol
                    order_q -= vol
                elif order_q == 0:
                    fully_ex = True
                    break
                i -= 1

            if not fully_ex:
                self._offers[p] += order_q

        return trades

    def get_col(self) -> Tuple[List[Tuple[int, int]], float]:
        """ Get LOB as a column of price, interest pairs with the midpoint price as a float"""
        ladder = []
        o = min([i[0] for i in enumerate(self._offers) if float(i[1]) != 0.0]) # lowest offer
        b = max([i[0] for i in enumerate(self._bids) if float(i[1]) != 0.0]) # highest bid
        mid: float = (o+b) / 2
        ladder.extend(list(enumerate(self._bids))[:int(mid)+1])
        if mid %1 != 0:
            ladder.append((mid, 0))
        ladder.extend(list(enumerate(self._offers))[math.ceil(mid):]) # add offers
        return ladder, mid

    def __repr__(self):
        return '\n-----\n'.join([str(i) for i in self.get_col()[0]])
