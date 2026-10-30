"""Run the pipeline: python -m interview_sandbox.benchmark_staff.pipeline"""

import json
import sqlite3
import sys
from contextlib import closing
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from interview_sandbox.benchmark_staff.normalize import SCHOOLS, StaffRecord, validate_records
from interview_sandbox.benchmark_staff.sources import (
    read_custom_html,
    read_previous_snapshot,
    read_sidearm,
    read_wmt,
)

PACKAGE_DIR = Path(__file__).parent
INPUT_DIR = PACKAGE_DIR / "inputs"
OUTPUT_DIR = PACKAGE_DIR / "output"
DB_PATH = Path("data/benchmark_staff.db")
SCHEMA_SQL = (PACKAGE_DIR / "sql" / "schema.sql").read_text()
CHANGE_REPORT_SQL = (PACKAGE_DIR / "sql" / "change_report.sql").read_text()


def read_current(input_dir: Path) -> list[StaffRecord]:
    return [
        *read_sidearm(input_dir / "sidearm_current.json"),
        *read_wmt(input_dir / "wmt_current.csv"),
        *read_custom_html(input_dir / "custom_current.html"),
    ]


def load_snapshot(con: sqlite3.Connection, snapshot_id: str, records: list[StaffRecord]) -> None:
    con.execute("INSERT INTO snapshots VALUES (?, NULL)", [snapshot_id])
    con.executemany(
        "INSERT INTO snapshot_coverage VALUES (?, ?)",
        [[snapshot_id, school_id] for school_id in sorted({r.school_id for r in records})],
    )
    con.executemany(
        "INSERT INTO staff_observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            [
                f"{snapshot_id}:{i}",
                snapshot_id,
                r.school_id,
                r.staff_id,
                r.name,
                r.name_key,
                r.title,
                r.title_raw,
                r.email,
                r.phone,
                r.source_provider,
                r.source_url,
            ]
            for i, r in enumerate(records)
        ],
    )


def build_database(
    con: sqlite3.Connection, previous: list[StaffRecord], current: list[StaffRecord]
) -> None:
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA_SQL)
    con.executemany("INSERT INTO schools VALUES (?, ?)", list(SCHOOLS.items()))
    load_snapshot(con, "previous", previous)
    load_snapshot(con, "current", current)
    con.commit()


def change_report(con: sqlite3.Connection) -> pd.DataFrame:
    params = {"prev_snapshot": "previous", "curr_snapshot": "current"}
    return pd.read_sql_query(CHANGE_REPORT_SQL, con, params=params)


def run(input_dir: Path = INPUT_DIR, db_path: str = ":memory:") -> tuple[list, pd.DataFrame]:
    previous = read_previous_snapshot(input_dir / "previous_snapshot.json")
    current = read_current(input_dir)

    errors, warnings = validate_records(current)
    for warning in warnings:
        print(f"WARNING {warning}", file=sys.stderr)
    if errors:
        raise ValueError("Validation failed:\n" + "\n".join(errors))

    with closing(sqlite3.connect(db_path)) as con:
        build_database(con, previous, current)
        report = change_report(con)
    return current, report


def main() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    DB_PATH.unlink(missing_ok=True)
    current, report = run(db_path=str(DB_PATH))
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "normalized_current.json").write_text(
        json.dumps([asdict(r) for r in current], indent=2) + "\n"
    )
    report.to_csv(OUTPUT_DIR / "change_report.csv", index=False)

    changes = report[report["change_type"] != "unchanged"]
    with pd.option_context("display.width", 250, "display.max_colwidth", 60):
        print(changes.drop(columns=["staff_id"]).fillna("").to_string(index=False))
    print(f"\n{len(changes)} changes, {len(report) - len(changes)} unchanged.")
    print(f"Wrote {OUTPUT_DIR}/normalized_current.json, change_report.csv and {DB_PATH}")


if __name__ == "__main__":
    main()
