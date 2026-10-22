"""The tables of ShopNest, written as SQLAlchemy models.

Read README.md first. This is the finished file.
"""
import enum
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class State(enum.Enum):
    """EXAMPLE, already finished."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Base(DeclarativeBase):
    """EXAMPLE, already finished. Every table gets the columns `id` and `state` from here."""

    id: Mapped[int] = mapped_column(primary_key=True)
    state: Mapped[State] = mapped_column(default=State.ACTIVE)


class Category(Base):
    """EXAMPLE, already finished."""

    __tablename__ = "category"

    name: Mapped[str] = mapped_column(String(100))


class Product(Base):
    """EXAMPLE, already finished. This is the model that we wrote in class."""

    __tablename__ = "product"

    title: Mapped[str] = mapped_column(String(200))
    price: Mapped[Decimal] = mapped_column(Numeric(19, 2))
    stock: Mapped[int]
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("category.id"))
    category: Mapped[Optional[Category]] = relationship()


class OrderLine(Base):
    """One line of an order = a product, how many were bought, and the price of ONE item."""

    __tablename__ = "order_line"

    # A short note. It can be empty (`Optional[...]`), and it is text of up to 200 characters.
    note: Mapped[Optional[str]] = mapped_column(String(200))

    # How many items were bought. `Mapped[int]` means: a whole number that is required (not empty).
    quantity: Mapped[int]

    # The price of ONE item. Numeric(19, 2) = up to 19 digits, 2 of them after the point (an exact number).
    # Without it, MySQL would make DECIMAL(10,0) and 9.99 would be saved as 10.
    unit_price: Mapped[Decimal] = mapped_column(Numeric(19, 2))

    # The id of the product. The foreign key makes MySQL check that this id exists in the table `product`.
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"))

    # Not a column: it lets us write `line.product` and get the Product object itself.
    product: Mapped[Product] = relationship()
