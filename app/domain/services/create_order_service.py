from app.domain.entities.order import Order
from app.domain.ports.order_repository_port import OrderRepositoryPort
from app.adapters.driven.gateways.product_catalog_gateway import ProductCatalogGateway

class CreateOrderService:
    def __init__(self, order_repo: OrderRepositoryPort, catalog: ProductCatalogGateway):
        self.order_repo = order_repo
        self.catalog = catalog

    def execute(self, order: Order) -> Order:
        total = 0
        for item in order.items:
            prod = self.catalog.get_product(item.product_id)
            if prod["stock"] < item.quantity:
                raise ValueError(
                    f"Estoque insuficiente para '{prod['name']}' "
                    f"(disponível {prod['stock']})"
                )
            self.catalog.reserve_stock(item.product_id, item.quantity)

            item.name = prod["name"]
            item.price = (prod["price"]) * (item.quantity)
            total += item.price

        order.amount = float(total)
        return self.order_repo.create(order)
