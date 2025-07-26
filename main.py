from fastapi import FastAPI
from app.adapters.driver.controllers.order_controller import router as order_router
from fastapi.security import OAuth2PasswordBearer, HTTPBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
bearer_scheme = HTTPBearer()


def create_app() -> FastAPI:
    app = FastAPI(title="Order Service")
    app.include_router(order_router, prefix="/api", tags=["orders"])
    return app

app = create_app()