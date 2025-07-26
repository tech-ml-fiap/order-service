import copy

from app.domain.entities.item import OrderItem
from app.domain.entities.order import Order
from app.shared.enums.order_status import OrderStatus


def test_order_item_defaults():
    item = OrderItem(product_id="SKU1", quantity=2)
    assert item.price == 0.0
    assert item.name is None
    assert item.id is None

def test_order_item_custom_values():
    item = OrderItem(product_id="SKU2", quantity=1, price=5.5, name="Fries", id=7)
    assert item.price == 5.5
    assert item.name == "Fries"
    assert item.id == 7

def test_order_item_dataclass_equality_and_copy():
    i1 = OrderItem(product_id="A", quantity=1)
    i2 = copy.deepcopy(i1)
    assert i1 == i2
    i2.quantity = 3
    assert i1 != i2


def test_order_defaults_and_relationship():
    order = Order()
    assert order.status == OrderStatus.RECEIVED
    assert order.items == []
    assert order.amount == 0.0

def test_order_add_items_and_total():
    order = Order(amount=0.0)
    order.items.append(OrderItem(product_id="X", quantity=2, price=4))
    order.items.append(OrderItem(product_id="Y", quantity=1, price=6))
    order.amount = sum(i.price for i in order.items)
    assert order.amount == 10.0
    assert len(order.items) == 2

def test_order_list_is_unique_per_instance():
    o1 = Order()
    o2 = Order()
    o1.items.append(OrderItem(product_id="Z", quantity=1))
    assert o2.items == []
