"""Build a sample e-commerce SQLite database. Run with: python -m interview_sandbox.sample_db"""

import random
import sqlite3
import sys
from pathlib import Path

from faker import Faker

DEFAULT_PATH = Path("data/sample.db")

SCHEMA = """
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    city        TEXT NOT NULL,
    signup_date TEXT NOT NULL
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    category   TEXT NOT NULL,
    price      REAL NOT NULL
);

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (customer_id),
    order_date  TEXT NOT NULL,
    status      TEXT NOT NULL CHECK (status IN ('pending', 'shipped', 'delivered', 'cancelled'))
);

CREATE TABLE order_items (
    order_id   INTEGER NOT NULL REFERENCES orders (order_id),
    product_id INTEGER NOT NULL REFERENCES products (product_id),
    quantity   INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL,
    PRIMARY KEY (order_id, product_id)
);
"""

CATEGORIES = ["Electronics", "Books", "Home", "Toys", "Clothing"]
STATUSES = ["pending", "shipped", "delivered", "cancelled"]
STATUS_WEIGHTS = [10, 20, 60, 10]


def build_sample_db(
    path: Path = DEFAULT_PATH,
    customers: int = 200,
    products: int = 30,
    orders: int = 1000,
    seed: int = 42,
) -> Path:
    """Create a fresh SQLite database at `path` filled with fake store data.

    The same seed always produces the same data.
    """
    fake = Faker()
    Faker.seed(seed)
    rng = random.Random(seed)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)

    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)

        conn.executemany(
            "INSERT INTO customers VALUES (?, ?, ?, ?, ?)",
            [
                (
                    i,
                    fake.name(),
                    fake.unique.email(),
                    fake.city(),
                    fake.date_between("-3y", "-1y").isoformat(),
                )
                for i in range(1, customers + 1)
            ],
        )

        product_rows = [
            (
                i,
                fake.unique.catch_phrase(),
                rng.choice(CATEGORIES),
                round(rng.uniform(5, 500), 2),
            )
            for i in range(1, products + 1)
        ]
        conn.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", product_rows)
        prices = {product_id: price for product_id, _, _, price in product_rows}

        order_rows = []
        item_rows = []
        for order_id in range(1, orders + 1):
            order_rows.append(
                (
                    order_id,
                    rng.randint(1, customers),
                    fake.date_between("-1y", "today").isoformat(),
                    rng.choices(STATUSES, STATUS_WEIGHTS)[0],
                )
            )
            for product_id in rng.sample(range(1, products + 1), k=rng.randint(1, 4)):
                item_rows.append((order_id, product_id, rng.randint(1, 5), prices[product_id]))

        conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", order_rows)
        conn.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?)", item_rows)

    conn.close()
    return path


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    path = build_sample_db(Path(args[0]) if args else DEFAULT_PATH)
    print(f"Created {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
