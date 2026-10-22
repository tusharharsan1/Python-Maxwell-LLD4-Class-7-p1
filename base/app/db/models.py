"""The tables of ShopNest, written as SQLAlchemy models.

Read README.md first. Your job is to finish the four fields marked TODO in `OrderLine`.
Do not change the other classes.
"""
import enum
from decimal import Decimal

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
    category_id: Mapped[int | None] = mapped_column(ForeignKey("category.id"))
    category: Mapped[Category | None] = relationship()


class OrderLine(Base):
    """TASK 1: one line of an order = a product, how many were bought, and the price of ONE item."""

    # EXAMPLES, already finished.
    __tablename__ = "order_line"

    # A short note. It can be empty (`| None`), and it is text of up to 200 characters.
    note: Mapped[str | None] = mapped_column(String(200))

    # TASK 1: add the four fields below, using the table in README.md.
    # TODO 1: quantity: a whole number, required.
    # TODO 2: unit_price: money, required. Use Numeric(19, 2), as `Product.price` does.
    # TODO 3: product_id: a whole number, required, and a foreign key to "product.id".
    # TODO 4: product: the relationship, so that `line.product` gives the Product object.
