"""Sanity check that the data libraries in requirements.txt are installed and work."""

import duckdb
import pandas as pd
import polars as pl
import pyarrow as pa
from sqlalchemy import create_engine, text


def test_pandas():
    df = pd.DataFrame({"x": [1, 2, 3]})
    assert df["x"].sum() == 6


def test_polars():
    df = pl.DataFrame({"x": [1, 2, 3]})
    assert df["x"].sum() == 6


def test_pyarrow():
    table = pa.table({"x": [1, 2, 3]})
    assert table.num_rows == 3


def test_duckdb_queries_pandas():
    con = duckdb.connect()
    con.register("numbers", pd.DataFrame({"x": [1, 2, 3]}))
    assert con.sql("SELECT SUM(x) FROM numbers").fetchall() == [(6,)]


def test_sqlalchemy_sqlite():
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        assert conn.execute(text("SELECT 1 + 1")).scalar() == 2
