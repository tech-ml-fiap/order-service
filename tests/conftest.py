# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import database as db

@pytest.fixture(autouse=True)
def _patch_session(monkeypatch):
    engine = create_engine("sqlite:///:memory:", future=True)
    TestingSession = sessionmaker(bind=engine, autoflush=False, future=True)

    db.Base.metadata.create_all(engine)

    monkeypatch.setattr(db, "SessionLocal", TestingSession)
