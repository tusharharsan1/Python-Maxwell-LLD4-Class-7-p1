> **Where the files are:** the starter files are in the `base/` folder. Every path below (such as `app/db/models.py` and `try_it.py`) is inside `base/`. Open a terminal in `base/` to run the commands.

# Order Lines at ShopNest

## Problem Statement
ShopNest wants to keep customers' orders in MySQL. An order is made of **lines**. Each line says which product was bought, how many items, and the price of **one** item at that moment. In class we turned Python classes into tables with SQLAlchemy, and we learned that **money must be exact**: `Decimal` in Python and `Numeric(19, 2)` in the column, never `float`. Now you do both. First finish the model `OrderLine` (a table). Then write a small function, `order_total`, that adds up the lines of an order **exactly**. Together they need only about 8 lines of code.

## Requirements
### The table `order_line` (the model `OrderLine`)
Every row of the table is one line of an order.

| Field | What it holds | Python type | In MySQL | Required? |
|---|---|---|---|---|
| `id` | the number of the line | `int` | primary key | comes from `Base` (already there) |
| `state` | `ACTIVE` or `INACTIVE` | `State` | enum | comes from `Base` (already there) |
| `note` | a short note | `str` | `VARCHAR(200)` | no, it can be empty (already written) |
| `quantity` | how many items | `int` | `INTEGER` | **yes** |
| `unit_price` | the price of ONE item | `Decimal` | `NUMERIC(19, 2)` | **yes** |
| `product_id` | which product was bought | `int` | a foreign key to `product.id` | **yes** |
| `product` | the product itself | `Product` | not a column: a relationship | not a column |

This is how the finished model is used (no database is needed for this assignment):
```python
product = Product(title="Essence Mascara Lash Princess", price=Decimal("9.99"), stock=99)
line = OrderLine(quantity=2, unit_price=Decimal("9.99"), product=product)
line.product.title      # "Essence Mascara Lash Princess"
```

Two things from class to remember:
- `Numeric(19, 2)` means up to 19 digits, with 2 digits after the point. If you write only `Mapped[Decimal]` and nothing else, MySQL would make the column `DECIMAL(10,0)`, and a price of `9.99` would be saved as `10`.
- The foreign key sits on the "many" side: the order line carries the id of its product. The product does not carry a list of lines.

### What `order_total` gives back
`order_total` receives a list of pairs: `(the price of ONE item, written as text, how many items)`. The prices are text, as they are in the JSON that comes from outside (for example `"9.99"`). It gives back one `Decimal`: the sum of `price × quantity` of all the lines, exact to the last digit.

| The lines | The answer |
|---|---|
| `[("9.99", 3)]` | `Decimal("29.97")` |
| `[("0.10", 10)]` | `Decimal("1.00")` |
| `[("9.99", 3), ("0.10", 10)]` | `Decimal("30.97")` |
| `[("0.1", 1), ("0.2", 1)]` | `Decimal("0.3")`, **exactly**, not `0.30000000000000004` |
| `[]` (an empty order) | zero (a `Decimal` that is equal to `0`) |

### The rules for `order_total`
- The answer is a `Decimal`, never a `float`.
- Each price is turned into a `Decimal` **from its text**. No `float` is used anywhere.
- The list that was passed in must not be changed.

To achieve these requirements we need to do 2 things:
- Finish the model `OrderLine`: add its four missing fields.
- Finish the function `order_total`.

## Instructions
1. We need to finish the class `OrderLine` inside `app/db/models.py`. There are four TODO notes in it (`TODO 1` to `TODO 4`): `quantity`, `unit_price`, `product_id` and `product`. The table name and `note` are already there as examples.
2. We need to implement the function `order_total` inside `app/services/order_service.py` (`TODO 5`).
3. `unit_price` must use `Numeric(19, 2)`, as `Product.price` does. A `Decimal` field without it is not accepted.
4. Do not modify `State`, `Base`, `Category`, `Product`, the example lines of `OrderLine` (`__tablename__` and `note`), the name of the function or its parameter. Feel free to add new methods or new functions if required.
5. When the TODO in `order_total` is finished, delete the `raise NotImplementedError(...)` line.
6. Run `python try_it.py` from this folder (the one that contains `app/` and `try_it.py`) to see what your code does. When both tasks are finished, you should see exactly this:
   ```
   Task 1: OrderLine
     table name           : order_line
     columns              : ['id', 'note', 'product_id', 'quantity', 'state', 'unit_price']
     quantity is required : True
     unit_price type      : NUMERIC(19, 2)
     product_id points to : product.id
     line.product.title   : Essence Mascara Lash Princess
     MySQL would add      : FOREIGN KEY(product_id) REFERENCES product (id)
   Task 2: order_total
     9.99 three times     : 29.97
     0.10 ten times       : 1.00
     0.1 and 0.2          : 0.3
     an empty order is 0  : True
     the answer is a      : Decimal
     two lines together   : 30.97
     input is unchanged   : True
   ```
   If you see `not done yet`, a task is not finished (a field is missing, or `order_total` still has its `raise` line).
7. Your code will be checked with the test file `tests/test_order_lines.py`. It checks the cases in the Requirements above, and the rules in instructions 3, 4 and 5. While you write your code, use `python try_it.py` (instruction 6) to check your work.
8. You do not need MySQL, a server, an internet connection or a key for this assignment. The model only **describes** the table, and nothing is ever created in a database. `sqlalchemy` is already installed (`pip install "sqlalchemy[asyncio]" asyncmy alembic` in Class 7). It works with Python 3.8 or newer.
9. Hints (all of these use ideas from class):
   - **The four fields (TODO 1 to TODO 4).** The first three are almost the same as lines you already know from `Product`:
     ```python
     quantity: Mapped[int]
     unit_price: Mapped[Decimal] = mapped_column(Numeric(19, 2))
     product_id: Mapped[int] = mapped_column(ForeignKey("product.id"))
     ```
     The fourth is the relationship, like `category` in `Product`. It points to the class `Product`, and it is **not** a column.
   - **A price from text (TODO 5).** Build a `Decimal` from a string, and multiply it by a whole number:
     ```python
     Decimal("9.99") * 3        # Decimal('29.97')
     ```
   - **A total that starts at zero.** Start with `total = Decimal("0")`, go through the lines with `for price, quantity in lines:`, add each line to `total`, and return `total`.
   - **If something looks wrong.** If `unit_price type` shows only `NUMERIC` (without `(19, 2)`), you forgot `Numeric(19, 2)`. If `0.1 and 0.2` shows `0.30000000000000004`, a `float` got in: build every `Decimal` from the **text** of the price. If `product_id points to` says `nothing yet`, the `ForeignKey("product.id")` is missing. If `try_it.py` says `app/db/models.py has a problem -> MappedAnnotationError`, the line for `product` has no `= relationship()` at the end. If it says `NoForeignKeysError`, the `ForeignKey("product.id")` is missing.
