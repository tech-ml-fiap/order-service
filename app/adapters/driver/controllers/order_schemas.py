from typing import Optional, List
from pydantic import BaseModel

from app.shared.enums.order_status import OrderStatus


class OrderItemIn(BaseModel):
    product_id: str
    quantity: int


class OrderIn(BaseModel):
    # coupon_hash: Optional[str] = None
    items: List[OrderItemIn]


class OrderItemOut(BaseModel):
    product_id: str
    name: str
    quantity: int
    price: float


class OrderOut(BaseModel):
    id: int
    client_id: Optional[int]
    # coupon_hash: Optional[str]
    status: OrderStatus
    items: List[OrderItemOut]
    amount: float

class OrderOutQrCode(BaseModel):
    id: int
    client_id: Optional[int]
    qr_code: Optional[str]
    status: OrderStatus
    items: List[OrderItemOut]
    amount: float