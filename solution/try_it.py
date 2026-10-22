"""Run this file to see what your code does:   python try_it.py

You do not need to change anything in this file.
"""
from decimal import Decimal

from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateTable

try:
    from app.db.models import OrderLine, Product
except Exception as error:   # a mistake in models.py stops SQLAlchemy right here
    raise SystemExit(f"app/db/models.py has a problem -> {type(error).__name__}: {str(error).splitlines()[0][:150]}")
from app.services.order_service import order_total

print("Task 1: OrderLine")
print("  table name           :", OrderLine.__tablename__)
columns = OrderLine.__table__.columns
print("  columns              :", sorted(columns.keys()))
missing = [name for name in ("quantity", "unit_price", "product_id", "product") if not hasattr(OrderLine, name)]
if missing:
    print("  not done yet ->", ", ".join(missing), "is missing")
else:
    print("  quantity is required :", not columns["quantity"].nullable)
    print("  unit_price type      :", columns["unit_price"].type)
    links = list(columns["product_id"].foreign_keys)
    print("  product_id points to :", links[0].target_fullname if links else "nothing yet (it needs a ForeignKey)")
    try:
        product = Product(title="Essence Mascara Lash Princess", price=Decimal("9.99"), stock=99)
        line = OrderLine(quantity=2, unit_price=Decimal("9.99"), product=product)
        print("  line.product.title   :", line.product.title)
        create = str(CreateTable(OrderLine.__table__).compile(dialect=mysql.dialect()))
        link = [text.strip().rstrip(",") for text in create.splitlines() if "FOREIGN KEY" in text]
        print("  MySQL would add      :", link[0] if link else "no foreign key yet")
    except Exception as error:
        print("  something is wrong ->", type(error).__name__ + ":", str(error).splitlines()[0][:150])

print("Task 2: order_total")
try:
    print("  9.99 three times     :", order_total([("9.99", 3)]))
    print("  0.10 ten times       :", order_total([("0.10", 10)]))
    print("  0.1 and 0.2          :", order_total([("0.1", 1), ("0.2", 1)]))
    print("  an empty order is 0  :", order_total([]) == 0)
    print("  the answer is a      :", type(order_total([("1.50", 2)])).__name__)
    lines = [("9.99", 3), ("0.10", 10)]
    before = list(lines)
    print("  two lines together   :", order_total(lines))
    print("  input is unchanged   :", lines == before)
except NotImplementedError as error:
    print("  not done yet ->", error)
