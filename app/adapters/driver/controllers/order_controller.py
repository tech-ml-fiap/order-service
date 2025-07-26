from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.adapters.driven.repositories.order import OrderRepository
from app.adapters.driven.gateways.product_catalog_gateway import ProductCatalogGateway
from app.domain.entities.order import Order
from app.domain.entities.item import OrderItem
from app.domain.services.create_order_service import CreateOrderService
from app.domain.services.list_order_service import ListOrdersService, GetOrderByIdService
from app.domain.services.update_order_service import UpdateOrderStatusService
from app.shared.enums.order_status import OrderStatus
from database import get_db_session
from .order_schemas import OrderIn, OrderOut, OrderItemOut

router = APIRouter()


@router.post("/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderIn,
    db: Session = Depends(get_db_session),
):
    order_repo = OrderRepository(db)
    catalog = ProductCatalogGateway()
    service = CreateOrderService(order_repo, catalog)

    domain_order = Order(
        client_id=None,
        items=[
            OrderItem(product_id=i.product_id, quantity=i.quantity)
            for i in payload.items
        ],
    )

    try:
        created = service.execute(domain_order)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return _to_out(created)


@router.get("/orders", response_model=List[OrderOut])
def list_orders(
    status: OrderStatus | None = Query(
        default=None,
        description="Filtra por status (omitido = todos)"
    ),
    db: Session = Depends(get_db_session),
):
    orders = ListOrdersService(OrderRepository(db)).execute(status=status)
    return [_to_out(o) for o in orders]


@router.get("/orders/{order_id}", response_model=OrderOut, status_code=200)
def get_order_by_id(
    order_id: int,
    db: Session = Depends(get_db_session),
):
    order = GetOrderByIdService(OrderRepository(db)).execute(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _to_out(order)


@router.patch(
    "/orders/{order_id}/status",
    response_model=OrderOut,
    status_code=status.HTTP_200_OK,
)
def update_order_status(
    order_id: int,
    status: OrderStatus = Query(..., description="Novo status do pedido"),
    db: Session = Depends(get_db_session),
):
    try:
        updated = UpdateOrderStatusService(OrderRepository(db)).execute(
            order_id, status
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _to_out(updated)

# ------------------------------------------------------------------ helpers
def _to_out(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        client_id=order.client_id,
        status=order.status,
        amount=order.amount,
        items=[
            OrderItemOut(
                product_id=i.product_id,
                name=i.name,
                quantity=i.quantity,
                price=i.price,
            )
            for i in order.items
        ],
    )
