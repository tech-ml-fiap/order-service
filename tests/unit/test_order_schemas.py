import pytest
from pydantic import ValidationError

from app.adapters.driver.controllers.order_schemas import OrderItemIn, OrderIn, OrderItemOut, OrderOut
from app.shared.enums.order_status import OrderStatus


def test_order_item_in_valid():
    item = OrderItemIn(product_id="SKU1", quantity=2)
    assert item.product_id == "SKU1"
    assert item.quantity == 2


def test_order_item_in_missing_field():
    with pytest.raises(ValidationError):
        OrderItemIn(product_id="SKU1")


def test_order_item_in_wrong_type():
    with pytest.raises(ValidationError):
        OrderItemIn(product_id="SKU1", quantity="two")


def test_order_in_valid():
    order = OrderIn(items=[OrderItemIn(product_id="X", quantity=1)])
    assert order.items[0].product_id == "X"


def test_order_in_empty_items():
    order = OrderIn(items=[])
    assert order.items == []


def test_order_item_out():
    out = OrderItemOut(product_id="Y", name="Burger", quantity=3, price=7.5)
    assert out.price == 7.5
    assert out.model_dump()["name"] == "Burger"

def test_order_out_with_client():
    order_out = OrderOut(
        id=1,
        client_id=42,
        status=OrderStatus.RECEIVED,
        amount=22.5,
        items=[
            OrderItemOut(product_id="Z", name="Soda", quantity=1, price=2.5),
        ],
    )
    assert order_out.client_id == 42
    assert order_out.items[0].quantity == 1


def test_order_out_without_client():
    order_out = OrderOut(
        id=2,
        client_id=None,
        status=OrderStatus.READY,
        amount=15.0,
        items=[
            OrderItemOut(product_id="A", name="Fries", quantity=2, price=5.0),
        ],
    )
    assert order_out.client_id is None
    assert order_out.status == OrderStatus.READY
