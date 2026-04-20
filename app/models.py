import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


def utcnow_naive() -> datetime:
    return datetime.utcnow()


# ---------- Shared / base ----------
class ItemBase(SQLModel):
    name: str = Field(max_length=255, index=True)
    description: str | None = Field(default=None, max_length=1024)
    price: float = Field(ge=0)
    is_available: bool = Field(default=True)


# ---------- DB table ----------
class Item(ItemBase, table=True):
    __tablename__ = "items"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow_naive)
    updated_at: datetime = Field(default_factory=utcnow_naive)


# ---------- Request schemas ----------
class ItemCreate(ItemBase):
    pass


class ItemUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1024)
    price: float | None = Field(default=None, ge=0)
    is_available: bool | None = None


# ---------- Response schemas ----------
class ItemRead(ItemBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
