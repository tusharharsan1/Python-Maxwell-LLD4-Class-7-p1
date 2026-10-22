"""Adds up the lines of an order.

This is the finished file.
"""
from decimal import Decimal
from typing import List, Tuple


def order_total(lines: List[Tuple[str, int]]) -> Decimal:
    """The total price of an order, exact to the last digit.

    `lines` is a list of pairs: (the price of ONE item written as text, how many were bought).
    Example: [("9.99", 3), ("0.10", 10)] means 3 items at 9.99 and 10 items at 0.10.
    The answer is a Decimal. An empty order costs zero.
    Do not use float, and do not change the list that was passed in.
    """
    # Start at zero. It is a Decimal, so an empty order gives a Decimal too (not the number 0).
    total = Decimal("0")
    for price, quantity in lines:
        # Build the Decimal from the TEXT of the price, such as "9.99". No float is used, so no error comes in.
        total = total + Decimal(price) * quantity
    return total
