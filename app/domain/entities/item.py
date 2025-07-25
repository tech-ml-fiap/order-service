from dataclasses import dataclass
from typing import Optional

@dataclass
class OrderItem:
    product_id: str
    quantity: int
    price: float = 0.0
    name: Optional[str] = None
    id: Optional[int] = None