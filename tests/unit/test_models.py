import datetime as dt

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.adapters.driven.models import OrderModel, OrderItemModel
from app.shared.enums.order_status import OrderStatus
from database import Base


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, future=True)
    with Session() as s:
        yield s
        s.close()


def test_order_defaults_and_timestamp(session):
    o = OrderModel(client_id=1, amount=0.0)
    session.add(o)
    session.commit()
    session.refresh(o)

    assert o.active is True

    assert isinstance(o.created_at, dt.datetime)
    assert isinstance(o.updated_at, dt.datetime)

    assert o.status == OrderStatus.RECEIVED

    rep = repr(o)
    assert "<OrderModel" in rep and "customer_id=1" in rep and "status=OrderStatus.RECEIVED" in rep

    # updated_at muda após alteração
    previous = o.updated_at
    o.amount = 9.9
    session.commit()
    session.refresh(o)
    assert o.updated_at >= previous


def test_item_relationship_and_repr(session):
    order = OrderModel(client_id=None, amount=15.0)
    session.add(order)
    session.commit()

    item = OrderItemModel(
        order_id=order.id,
        product_id="SKU123",
        product_name="Burger",
        quantity=2,
        price=7.5,
    )
    session.add(item)
    session.commit()
    session.refresh(item)

    assert item.order is order
    assert order.items == [item]

    # BaseModel default
    assert item.active is True

    # __repr__
    rep = repr(item)
    assert "order_id" in rep and "SKU123" in rep and "quantity=2" in rep
