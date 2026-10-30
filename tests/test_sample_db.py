import sqlite3

from interview_sandbox.sample_db import build_sample_db


def test_builds_expected_row_counts(tmp_path):
    path = build_sample_db(tmp_path / "sample.db", customers=20, products=5, orders=50)
    with sqlite3.connect(path) as conn:
        counts = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("customers", "products", "orders")
        }
        items = conn.execute("SELECT COUNT(*) FROM order_items").fetchone()[0]
    conn.close()
    assert counts == {"customers": 20, "products": 5, "orders": 50}
    assert 50 <= items <= 200


def test_foreign_keys_are_valid(tmp_path):
    path = build_sample_db(tmp_path / "sample.db", customers=20, products=5, orders=50)
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    conn.close()


def test_same_seed_gives_same_data(tmp_path):
    query = "SELECT * FROM orders ORDER BY order_id"
    first = build_sample_db(tmp_path / "a.db", customers=20, products=5, orders=50)
    second = build_sample_db(tmp_path / "b.db", customers=20, products=5, orders=50)
    with sqlite3.connect(first) as a, sqlite3.connect(second) as b:
        assert a.execute(query).fetchall() == b.execute(query).fetchall()
    a.close()
    b.close()


def test_rebuild_replaces_existing_file(tmp_path):
    path = tmp_path / "sample.db"
    build_sample_db(path, customers=20, products=5, orders=50)
    build_sample_db(path, customers=10, products=5, orders=50)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 10
    conn.close()
