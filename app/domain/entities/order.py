from dataclasses import dataclass, field
from typing import Optional, List
from app.domain.entities.item import OrderItem
from app.shared.enums.order_status import OrderStatus


@dataclass
class Order:
    id: Optional[int] = None
    client_id: Optional[int] = None
    status: OrderStatus = OrderStatus.RECEIVED
    # coupon_hash: Optional[str] = None
    # coupon_id: Optional[int] = None
    items: List[OrderItem] = field(default_factory=list)
    amount: Optional[float] = 0.0