from sqlalchemy import Column, Boolean
from app.shared.mixins.timestamp_mixin import TimestampMixin
from database import Base

class BaseModel(TimestampMixin, Base):
    __abstract__ = True
    active = Column(Boolean, default=True, nullable=False)

