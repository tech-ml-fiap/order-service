import traceback

from fastapi import FastAPI
from app.adapters.driver.controllers.order_controller import router as order_router
from fastapi.security import OAuth2PasswordBearer, HTTPBearer

from database import SQLALCHEMY_DATABASE_URL, engine

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
bearer_scheme = HTTPBearer()


def create_app() -> FastAPI:
    app = FastAPI(title="Order Service")
    app.include_router(order_router, prefix="/api", tags=["orders"])
    return app

app = create_app()

import os

for key in ["DB_USER", "DB_PASS", "DB_HOST", "DB_NAME"]:
    print(f"{key} = {repr(os.getenv(key))}")

print("SQLALCHEMY_DATABASE_URL =", SQLALCHEMY_DATABASE_URL)

try:
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception as e:
    print("ERRO DE CONEXÃO EXTERNA:", e)
    traceback.print_exc()

