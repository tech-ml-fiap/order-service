from app.domain.entities.order import Order
from app.domain.ports.customer_auth_port import CustomerAuthPort
from app.domain.ports.order_repository_port import OrderRepositoryPort
from app.adapters.driven.gateways.product_catalog_gateway import ProductCatalogGateway
from app.domain.ports.payment_status_port import PaymentGatewayPort

class CreateOrderService:
    def __init__(
        self,
        order_repo: OrderRepositoryPort,
        catalog: ProductCatalogGateway,
        payment_gateway: PaymentGatewayPort,
            customer_auth: CustomerAuthPort
    ):
        self.order_repo = order_repo
        self.catalog = catalog
        self.payment_gateway = payment_gateway
        self.customer_auth = customer_auth

    def execute(self, order: Order,token: str | None):
        if token:
            order.client_id = self.customer_auth.verify_token(token)
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
            item.price = prod["price"] * item.quantity
            total += item.price

        order.amount = float(total)

        # 1) persiste o pedido
        order = self.order_repo.create(order)

        # 2) dispara criação do pagamento
        qr_code, _ = self.payment_gateway.create_payment(order.id, order.amount)

        return [order, qr_code]
