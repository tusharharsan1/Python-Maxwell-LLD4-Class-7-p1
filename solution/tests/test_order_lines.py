import ast
import inspect
import os
import random
import sys
import unittest
import warnings
from decimal import Decimal
from fractions import Fraction
from unittest import mock

from sqlalchemy import Integer, Numeric, create_engine
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable

# Lets this file run directly (python tests/test_order_lines.py) from any folder.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.models import Base, Category, OrderLine, Product, State
from app.services import order_service
from app.services.order_service import order_total

# ---------------------------------------------------------------------------
# Test data: what the README says the tables look like
# ---------------------------------------------------------------------------

# Every column of the table `order_line`, as the README table lists them.
ORDER_LINE_COLUMNS = {"id", "state", "note", "quantity", "unit_price", "product_id"}

# The README examples for order_total: (the lines, the exact answer).
README_EXAMPLES = [
    ([("9.99", 3)], Decimal("29.97")),
    ([("0.10", 10)], Decimal("1.00")),
    ([("9.99", 3), ("0.10", 10)], Decimal("30.97")),
    ([("0.1", 1), ("0.2", 1)], Decimal("0.3")),
    ([], Decimal("0")),
]


# ---------------------------------------------------------------------------
# Helpers: keep the tests short and readable
# ---------------------------------------------------------------------------

def _columns(model):
    """The columns of the table of `model`, by name."""
    return model.__table__.columns


def _mysql_type(column):
    """The type of a column, written the way MySQL would write it (for example 'NUMERIC(19, 2)')."""
    return column.type.compile(dialect=mysql.dialect())


def _create_table_text(model):
    """The CREATE TABLE statement that MySQL would run for `model`, on one line per column."""
    return str(CreateTable(model.__table__).compile(dialect=mysql.dialect()))


def _link_targets(column):
    """The names of the columns that a column points to with a foreign key (for example ['product.id'])."""
    return sorted(key.target_fullname for key in column.foreign_keys)


def sa_relationship_names(model):
    """The names of the relationships that SQLAlchemy knows for `model`."""
    return set(model.__mapper__.relationships.keys())


def _in_memory_session():
    """A session on a throw-away database in memory (SQLite), with all the tables created.

    SQLite is used only to check that the foreign key and the relationship really connect two rows.
    SQLite has no exact DECIMAL and warns about it, so the warning is silenced: the price is not what is tested here.
    """
    engine = create_engine("sqlite://")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        Base.metadata.create_all(engine)
    return Session(engine)


def _a_product():
    """A new Product object, like the one in the README."""
    return Product(title="Essence Mascara Lash Princess", price=Decimal("9.99"), stock=99)


def _function_node():
    """The syntax tree of the function `order_total` (read from the source file of the student)."""
    tree = ast.parse(inspect.getsource(order_service))
    return next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "order_total")


# ===========================================================================
# TASK 1: the model OrderLine
# ===========================================================================

class OrderLineModelTests(unittest.TestCase):
    """Checks the table that the model OrderLine describes. No database is needed for these tests."""

    def test_the_table_is_called_order_line(self):
        """The table name is `order_line`."""
        self.assertEqual(OrderLine.__tablename__, "order_line")
        self.assertEqual(OrderLine.__table__.name, "order_line")

    def test_the_table_has_exactly_the_columns_of_the_readme(self):
        """The six columns of the README table are there, and no other column.

        Anti-bypass: `product` must NOT be in this set, because it is a relationship and not a column.
        """
        self.assertEqual(set(_columns(OrderLine).keys()), ORDER_LINE_COLUMNS)

    def test_quantity_is_a_required_whole_number(self):
        """`quantity` is an INTEGER that cannot be empty."""
        column = _columns(OrderLine)["quantity"]
        self.assertEqual(_mysql_type(column), "INTEGER")
        self.assertFalse(column.nullable, "quantity must be required")

    def test_unit_price_is_numeric_19_2(self):
        """`unit_price` is `Numeric(19, 2)`: 19 digits, 2 after the point, and it gives back a Decimal."""
        column = _columns(OrderLine)["unit_price"]
        self.assertIsInstance(column.type, Numeric)
        with self.subTest("precision and scale"):
            self.assertEqual((column.type.precision, column.type.scale), (19, 2))
        with self.subTest("it gives back a Decimal, not a float"):
            self.assertTrue(column.type.asdecimal)
        with self.subTest("what MySQL would build"):
            self.assertIn(_mysql_type(column), ("NUMERIC(19, 2)", "DECIMAL(19, 2)"))

    def test_unit_price_is_required(self):
        """`unit_price` cannot be empty."""
        self.assertFalse(_columns(OrderLine)["unit_price"].nullable, "unit_price must be required")

    def test_product_id_is_a_required_whole_number(self):
        """`product_id` is an INTEGER that cannot be empty."""
        column = _columns(OrderLine)["product_id"]
        self.assertEqual(_mysql_type(column), "INTEGER")
        self.assertFalse(column.nullable, "product_id must be required")

    def test_product_id_is_a_foreign_key_to_product_id(self):
        """`product_id` has a foreign key that points to the column `product.id`."""
        self.assertEqual(_link_targets(_columns(OrderLine)["product_id"]), ["product.id"])

    def test_product_is_a_relationship_not_a_column(self):
        """`product` is a relationship. It does not make a column of its own.

        Anti-bypass: the relationship must be known to SQLAlchemy (not a plain attribute that was added by hand).
        """
        self.assertNotIn("product", _columns(OrderLine).keys())
        self.assertIn("product", sa_relationship_names(OrderLine))

    def test_the_relationship_gives_one_product(self):
        """`line.product` is ONE Product (many lines can point to the same product)."""
        relationship = OrderLine.__mapper__.relationships["product"]
        with self.subTest("it points to the class Product"):
            self.assertIs(relationship.mapper.class_, Product)
        with self.subTest("many lines, one product"):
            self.assertEqual(relationship.direction.name, "MANYTOONE")

    def test_the_example_note_is_unchanged(self):
        """`note` is still the example from the starter: text of up to 200 characters, and it can be empty."""
        column = _columns(OrderLine)["note"]
        self.assertEqual(_mysql_type(column), "VARCHAR(200)")
        self.assertTrue(column.nullable)

    def test_id_and_state_come_from_base(self):
        """`id` is the primary key, and `state` starts as ACTIVE, both coming from `Base`."""
        columns = _columns(OrderLine)
        with self.subTest("id is the primary key"):
            self.assertTrue(columns["id"].primary_key)
        with self.subTest("state starts as ACTIVE"):
            self.assertIs(columns["state"].default.arg, State.ACTIVE)

    def test_the_create_table_statement_for_mysql(self):
        """The statement that MySQL would run has the three required columns and the foreign key.

        Anti-bypass: this reads the real statement that SQLAlchemy writes, so it cannot be passed by naming things.
        """
        text = _create_table_text(OrderLine)
        for expected in (
            "CREATE TABLE order_line",
            "quantity INTEGER NOT NULL",
            "product_id INTEGER NOT NULL",
            "FOREIGN KEY(product_id) REFERENCES product (id)",
        ):
            with self.subTest(expected):
                self.assertIn(expected, text)
        with self.subTest("unit_price"):
            # NUMERIC and DECIMAL are two names for the same exact number in MySQL.
            self.assertTrue("unit_price NUMERIC(19, 2) NOT NULL" in text or "unit_price DECIMAL(19, 2) NOT NULL" in text, text)

    def test_a_line_is_built_as_in_the_readme(self):
        """The README example works: a line made with `product=` gives that product back."""
        product = _a_product()
        line = OrderLine(quantity=2, unit_price=Decimal("9.99"), product=product)
        self.assertIs(line.product, product)
        self.assertEqual(line.product.title, "Essence Mascara Lash Princess")
        self.assertEqual(line.quantity, 2)
        self.assertEqual(line.unit_price, Decimal("9.99"))

    def test_saving_a_line_fills_product_id(self):
        """When a line is saved with its product, `product_id` becomes the id of that product.

        Anti-bypass: this saves real rows (in memory), so the foreign key and the relationship must really work together.
        """
        with _in_memory_session() as session:
            product = _a_product()
            line = OrderLine(quantity=2, unit_price=Decimal("9.99"), product=product)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                session.add(line)
                session.commit()
            self.assertIsNotNone(product.id)
            self.assertEqual(line.product_id, product.id)

    def test_a_saved_line_finds_its_product_again(self):
        """After saving, a new session can read the line and walk from the line to its product."""
        with _in_memory_session() as session:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                session.add(OrderLine(quantity=1, unit_price=Decimal("4.50"), product=_a_product()))
                session.commit()
            session.expire_all()
            line = session.get(OrderLine, 1)
            self.assertEqual(line.product.title, "Essence Mascara Lash Princess")


# ===========================================================================
# The rest of the file must not be changed (instruction 4 of the README)
# ===========================================================================

class UntouchedCodeTests(unittest.TestCase):
    """Checks that the example classes of the starter file were not modified."""

    def test_state_is_unchanged(self):
        """`State` still has exactly ACTIVE and INACTIVE."""
        self.assertEqual([member.name for member in State], ["ACTIVE", "INACTIVE"])

    def test_base_still_gives_id_and_state_to_every_table(self):
        """`Base` still gives every table an `id` (the primary key) and a `state` (ACTIVE or INACTIVE, starting as ACTIVE)."""
        for name, table in Base.metadata.tables.items():
            with self.subTest(table=name):
                self.assertTrue(table.columns["id"].primary_key)
                self.assertEqual(_mysql_type(table.columns["id"]), "INTEGER")
                self.assertEqual(_mysql_type(table.columns["state"]), "ENUM('ACTIVE','INACTIVE')")
                self.assertIs(table.columns["state"].default.arg, State.ACTIVE)

    def test_category_is_unchanged(self):
        """`Category` has its three columns and no relationship."""
        columns = _columns(Category)
        self.assertEqual(set(columns.keys()), {"id", "state", "name"})
        self.assertEqual(_mysql_type(columns["name"]), "VARCHAR(100)")
        self.assertEqual(sa_relationship_names(Category), set())

    def test_product_is_unchanged(self):
        """`Product` has its seven columns and only the relationship `category`.

        Anti-bypass: a list of lines on the product (a second relationship) is not part of this assignment.
        """
        columns = _columns(Product)
        self.assertEqual(set(columns.keys()), {"id", "state", "title", "price", "stock", "category_id"})
        with self.subTest("title"):
            self.assertEqual(_mysql_type(columns["title"]), "VARCHAR(200)")
        with self.subTest("price"):
            self.assertEqual(_mysql_type(columns["price"]), "NUMERIC(19, 2)")
        with self.subTest("stock"):
            self.assertEqual(_mysql_type(columns["stock"]), "INTEGER")
        with self.subTest("category_id points to category.id"):
            self.assertEqual(_link_targets(columns["category_id"]), ["category.id"])
        with self.subTest("only one relationship"):
            self.assertEqual(sa_relationship_names(Product), {"category"})

    def test_there_are_exactly_three_tables(self):
        """The models describe `category`, `product` and `order_line`, and nothing else."""
        self.assertEqual(set(Base.metadata.tables), {"category", "product", "order_line"})


# ===========================================================================
# TASK 2: the function order_total
# ===========================================================================

class OrderTotalTests(unittest.TestCase):
    """Checks that order_total adds up the lines exactly."""

    def test_the_readme_examples(self):
        """Every example of the README table gives its exact answer."""
        for lines, expected in README_EXAMPLES:
            with self.subTest(lines=lines):
                self.assertEqual(order_total(lines), expected)

    def test_the_answer_is_a_decimal(self):
        """The answer is a Decimal: not a float, not an int, not text."""
        answer = order_total([("1.50", 2)])
        self.assertIsInstance(answer, Decimal)
        self.assertNotIsInstance(answer, (float, int, str))

    def test_an_empty_order_is_a_decimal_zero(self):
        """An empty order costs zero, and that zero is a Decimal too.

        Anti-bypass: `sum(...)` without a starting Decimal gives the whole number 0, which is not a Decimal.
        """
        answer = order_total([])
        self.assertIsInstance(answer, Decimal)
        self.assertEqual(answer, 0)

    def test_point_one_and_point_two_make_exactly_point_three(self):
        """The Vancouver problem: 0.1 + 0.2 must be exactly 0.3, not 0.30000000000000004."""
        answer = order_total([("0.1", 1), ("0.2", 1)])
        self.assertEqual(answer, Decimal("0.3"))
        self.assertNotEqual(str(answer), "0.30000000000000004")

    def test_ten_times_ten_paise_is_exactly_one(self):
        """Ten items at 0.10 cost exactly 1 (the float answer is 0.9999999999999999 for ten additions of 0.1)."""
        lines = [("0.1", 1)] * 10
        self.assertEqual(order_total(lines), Decimal("1.0"))

    def test_a_price_that_a_float_cannot_hold(self):
        """A price with 19 digits keeps every digit (a float keeps only about 16).

        Anti-bypass: turning the text into a float first loses the last digits.
        """
        self.assertEqual(order_total([("12345678901234567.89", 3)]), Decimal("37037036703703703.67"))

    def test_quantity_zero_adds_nothing(self):
        """A line with quantity 0 adds nothing to the total."""
        self.assertEqual(order_total([("9.99", 0), ("1.25", 2)]), Decimal("2.50"))

    def test_digits_after_the_point_are_not_rounded(self):
        """The total is exact: nothing is rounded to 2 digits."""
        with self.subTest("three digits"):
            self.assertEqual(order_total([("0.125", 1)]), Decimal("0.125"))
        with self.subTest("many digits"):
            self.assertEqual(order_total([("0.001", 3), ("0.0001", 5)]), Decimal("0.0035"))

    def test_many_random_orders_match_an_exact_calculation(self):
        """200 random orders are checked against an independent exact calculation (fractions).

        Anti-bypass: the orders are made by the test, so a function that only knows the README examples fails here.
        """
        generator = random.Random(7)
        for _ in range(200):
            lines = []
            for _ in range(generator.randint(0, 8)):
                digits = generator.randint(0, 4)
                price = f"{generator.randint(0, 10 ** 12)}.{generator.randint(0, 10 ** digits - 1):0{max(digits, 1)}d}"
                lines.append((price, generator.randint(0, 1000)))
            exact = sum((Fraction(price) * quantity for price, quantity in lines), Fraction(0))
            with self.subTest(lines=lines):
                self.assertEqual(Fraction(order_total(lines)), exact)

    def test_the_order_of_the_lines_does_not_matter(self):
        """The same lines in another order give the same total."""
        lines = [("9.99", 3), ("0.10", 10), ("0.1", 1), ("0.2", 1), ("12.50", 4)]
        shuffled = list(reversed(lines))
        self.assertEqual(order_total(lines), order_total(shuffled))

    def test_the_list_is_not_changed(self):
        """The list that was passed in has the same pairs, in the same order, after the call.

        Anti-bypass: sorting, reversing, emptying or popping the list would be seen here.
        """
        lines = [("9.99", 3), ("0.10", 10), ("1.25", 2)]
        before = list(lines)
        order_total(lines)
        self.assertEqual(lines, before)

    def test_calling_twice_gives_the_same_answer(self):
        """The same list can be used twice (nothing is kept or used up between the calls)."""
        lines = [("9.99", 3), ("0.10", 10)]
        self.assertEqual(order_total(lines), order_total(lines))

    def test_no_float_is_used_while_it_runs(self):
        """While order_total runs, the built-in `float` is never called.

        Anti-bypass: `float` is replaced by a function that fails when it is used, for the length of one call.
        """
        with mock.patch("builtins.float", side_effect=AssertionError("float was used")):
            self.assertEqual(order_total([("9.99", 3), ("0.1", 1)]), Decimal("30.07"))

    def test_the_source_has_no_float(self):
        """The code of order_total has no `float` and no number written with a point (such as 0.5).

        Anti-bypass: words inside comments and in the text that explains the function are ignored.
        """
        function = _function_node()
        for node in ast.walk(function):
            if isinstance(node, ast.Name) and node.id == "float":
                self.fail("order_total uses float")
            if isinstance(node, ast.Constant) and isinstance(node.value, float):
                self.fail(f"order_total uses the float number {node.value!r}")

    def test_the_function_keeps_its_name_and_parameter(self):
        """The function is still called `order_total`, and its parameter is still called `lines`."""
        self.assertEqual(list(inspect.signature(order_total).parameters), ["lines"])


# ===========================================================================
# Run all tests
# ===========================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
