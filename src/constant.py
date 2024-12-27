from enum import Enum

class Direction(Enum):
    """
    Direction of order/trade/position.
    """
    LONG = 1
    SHORT = 2

class Offset(Enum):
    """
    Offset of order/trade.
    """
    NONE = 0
    OPEN = 1
    CLOSE = 2
    CLOSETODAY = 3

class Status(Enum):
    """
    Order status.
    """
    SUBMITTING = 1
    NOTTRADED = 2
    PARTTRADED = 3
    ALLTRADED = 4
    CANCELLED = 5
    REJECTED = 6

class OrderType(Enum):
    """
    Order type.
    """
    LIMIT = 1
    MARKET = 2
    STOP = 3
    FAK = 4
    FOK = 5