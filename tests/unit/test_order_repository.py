import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.adapters.driven.repositories.order import OrderRepository
from app.domain.entities.order import Order
from app.domain.entities.item import OrderItem
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


def _sample_order(client: int | None = 1, status=OrderStatus.RECEIVED) -> Order:
    return Order(
        client_id=client,
        status=status,
        amount=10.0,
        items=[OrderItem(product_id="SKU", name="Burger", quantity=1, price=10.0)],
    )


def test_crud_flow(session):
    repo = OrderRepository(session)

    created = repo.create(_sample_order())
    assert created.id is not None
    assert created.items[0].name == "Burger"

    fetched = repo.find_by_id(created.id)
    assert fetched.amount == 10.0

    assert len(repo.find_all()) == 1
    assert repo.find_all(status=OrderStatus.READY) == []

    created.status = OrderStatus.READY
    created.items[0].quantity = 3
    created.amount = 30.0
    updated = repo.update(created)
    assert updated.status == OrderStatus.READY
    assert updated.items[0].quantity == 3
    assert repo.find_all(status=OrderStatus.READY)[0].id == created.id

    repo.delete(created.id)
    assert repo.find_by_id(created.id) is None


def test_find_by_client(session):
    repo = OrderRepository(session)
    repo.create(_sample_order(client=1))
    repo.create(_sample_order(client=2))
    assert len(repo.find_by_client(1)) == 1
    assert len(repo.find_by_client(2)) == 1
    assert len(repo.find_by_client(3)) == 0


def test_update_nonexistent(session):
    repo = OrderRepository(session)
    with pytest.raises(ValueError):
        repo.update(Order(id=999, client_id=None, status=OrderStatus.RECEIVED, amount=0, items=[]))


def test_delete_nonexistent_is_noop(session):
    repo = OrderRepository(session)
    repo.delete(123)
    assert repo.find_by_id(123) is None
