from dataclasses import dataclass
from decimal import Decimal
from enum import Flag, auto
from copy import copy


class OrderStatus(Flag):
    """
     The possible states of an order:

    - INITIAL -> ACTIVE -> FILLED | CANCELLED | EXPIRED
    - INITIAL -> REJECTED
    """

    INITIAL = auto()
    ACTIVE = auto()
    REJECTED = auto()
    FILLED = auto()
    CANCELLED = auto()
    EXPIRED = auto()

    _OPEN = INITIAL | ACTIVE
    _CLOSE = REJECTED | FILLED | CANCELLED | EXPIRED

    @property
    def open(self):
        """Return True is the status is open, False otherwise"""
        return self in OrderStatus._OPEN

    @property
    def closed(self):
        """Return True is the status is closed, False otherwise"""
        return self in OrderStatus._CLOSE

    def __repr__(self) -> str:
        return self.name  # type: ignore


@dataclass
class Order:
    """
    A trading order. Default is a market order when only the size th specified. But optional a limit can be specified,
    making it a limit order.

    The id is automatically assigned by the broker and should not be set manually.
    """

    symbol: str
    size: Decimal
    limit: float | None
    id: str | None
    status: OrderStatus
    fill: Decimal

    def __init__(self, symbol: str, size: Decimal | str | int | float, limit: float | None = None):
        self.symbol = symbol
        self.size = Decimal(size)
        assert not self.size.is_zero(), "Cannot create a new order with size is zero"

        self.limit = limit
        self.id: str | None = None
        self.status: OrderStatus = OrderStatus.INITIAL
        self.fill = Decimal(0)

    @property
    def open(self) -> bool:
        """Return True is this order is open, False otherwise"""
        return self.status.open

    @property
    def closed(self) -> bool:
        """Return True is this order is closed, False otherwise"""
        return self.status.closed

    def cancel(self) -> "Order":
        """Create a cancellation order. You can only cancel orders that are still open and have an id.
        The returned order looks like a regular order, but with its size set to zero.
        """
        assert self.id is not None, "Can only cancel orders with an id"
        assert self.open, "Can only cancel open orders"

        result = copy(self)
        result.size = Decimal(0)
        return result

    def update(self, size: Decimal | str | int | float | None = None, limit: float | None = None) -> "Order":
        """Create an update-order. You can update the size and/or limit of an order. The returned order has the same id
        as the original order.

        You can only update existing orders that are still open and have an id.
        """

        assert self.id is not None, "Can only update orders with an id"
        assert self.open, "Can only update open orders"
        if limit:
            assert self.limit, "Can only update the limit if it has already a limit defined"

        size = Decimal(size) if size is not None else None
        if size is not None:
            assert not size.is_zero(), "size cannot be set to zero, use order.cancel() instead"

        result = copy(self)
        result.size = size or result.size
        result.limit = limit or result.limit
        return result

    def __copy__(self):
        result = Order(self.symbol, self.size, self.limit)
        result.id = self.id
        result.status = self.status
        result.fill = self.fill
        return result

    @property
    def is_cancellation(self):
        """Return True if this is a cancellation order, False otherwise"""
        return self.size.is_zero()

    @property
    def is_buy(self):
        """Return True if this is a BUY order, False otherwise"""
        return self.size > 0

    @property
    def is_sell(self):
        """Return True if this is a SELL order, False otherwise"""
        return self.size < 0
