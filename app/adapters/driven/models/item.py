from sqlalchemy import Column, Integer, ForeignKey, Float, String
from sqlalchemy.orm import relationship

from app.adapters.driven.models.base_model import BaseModel


class OrderItemModel(BaseModel):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    product_id = Column(String(50), nullable=False)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price = Column(Float, nullable=False)

    order = relationship("OrderModel", back_populates="items")

    def __repr__(self):
        return f"<OrderItemModel(order_id={self.order_id}, product_id={self.product_id}, quantity={self.quantity})>"
