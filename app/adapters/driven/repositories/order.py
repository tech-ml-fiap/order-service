from typing import List, Optional

from sqlalchemy import case
from sqlalchemy.orm import Session

from app.adapters.driven.models.order import OrderModel
from app.adapters.driven.models.item import OrderItemModel
from app.domain.entities.item import OrderItem
from app.domain.entities.order import Order
from app.domain.ports.order_repository_port import OrderRepositoryPort
from app.shared.enums.order_status import OrderStatus


class OrderRepository(OrderRepositoryPort):
    def __init__(self, db_session: Session):
        self.db = db_session

    def create(self, order: Order) -> Order:
        order_model = OrderModel(
            client_id=order.client_id,
            status=order.status,
            amount=order.amount,
        )
        self.db.add(order_model)
        self.db.flush()

        item_models: list[OrderItemModel] = []
        for item in order.items:
            im = OrderItemModel(
                order_id=order_model.id,
                product_id=item.product_id,
                product_name=item.name,
                quantity=item.quantity,
                price=item.price,
            )
            self.db.add(im)
            item_models.append(im)

        self.db.commit()
        self.db.refresh(order_model)

        return self._to_entity(order_model, item_models)

    def find_by_id(self, order_id: int) -> Optional[Order]:
        model = self.db.get(OrderModel, order_id)
        return self._to_entity(model) if model else None

    def find_all(self, status: Optional[OrderStatus] = None) -> List[Order]:
        q = self.db.query(OrderModel)
        if status is not None:
            q = q.filter(OrderModel.status == status)
        return [self._to_entity(m) for m in q.all()]

    def find_active_sorted_orders(self) -> List[Order]:
        status_priority = case(
            (OrderModel.status == OrderStatus.READY, 1),
            (OrderModel.status == OrderStatus.IN_PROGRESS, 2),
            (OrderModel.status == OrderStatus.RECEIVED, 3),
            else_=9999
        )

        order_models = (
            self.db.query(OrderModel)
            .filter(OrderModel.status != OrderStatus.COMPLETED)
            .filter(OrderModel.active == True)
            .order_by(status_priority, OrderModel.id.asc())
            .all()
        )
        return [self._to_entity(o) for o in order_models]

    def find_by_client(self, client_id: int) -> List[Order]:
        q = self.db.query(OrderModel).filter(OrderModel.client_id == client_id)
        return [self._to_entity(m) for m in q.all()]

    def update(self, order: Order) -> Order:
        model = self.db.get(OrderModel, order.id)
        if not model:
            raise ValueError("Order not found")

        model.status = order.status or model.status
        # model.coupon_id = order.coupon_id or model.coupon_id
        model.amount = order.amount or model.amount

        self.db.query(OrderItemModel).filter(OrderItemModel.order_id == model.id).delete()
        for item in order.items:
            self.db.add(
                OrderItemModel(
                    order_id=model.id,
                    product_id=item.product_id,
                    product_name=item.name,
                    quantity=item.quantity,
                    price=item.price,
                )
            )

        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def delete(self, order_id: int) -> None:
        model = self.db.get(OrderModel, order_id)
        if model:
            self.db.delete(model)
            self.db.commit()

    def _to_entity(
        self,
        model: OrderModel,
        eager_items: Optional[List[OrderItemModel]] = None,
    ) -> Order:
        items_models = eager_items if eager_items is not None else model.items
        return Order(
            id=model.id,
            client_id=model.client_id,
            status=model.status,
            # coupon_id=model.coupon_id,
            amount=model.amount,
            items=[
                OrderItem(
                    id=im.id,
                    product_id=im.product_id,
                    name=im.product_name,
                    quantity=im.quantity,
                    price=im.price,
                )
                for im in items_models
            ],
        )
