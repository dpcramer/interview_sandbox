import sqlite3
from contextlib import closing

import pytest

from interview_sandbox.normalize import (
    build_record,
    name_key,
    normalize_phone,
    normalize_school,
    normalize_title,
    validate_records,
)
from interview_sandbox.pipeline import build_database, change_report, run


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Assoc. AD / Compliance", "Associate Athletic Director, Compliance"),
        ("Dir., Football Operations", "Director, Football Operations"),
        ("Director of Football Operations", "Director, Football Operations"),
        ("Asst. Director, Athletic Communications", "Assistant Director, Athletic Communications"),
        (
            "Assistant Director - Strength & Conditioning",
            "Assistant Director, Strength and Conditioning",
        ),
        ("  Sports   Dietitian ", "Sports Dietitian"),
        (None, None),
    ],
)
def test_normalize_title(raw, expected):
    assert normalize_title(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Indiana", "indiana"),
        ("Indiana University", "indiana"),
        ("Notre Dame", "notre-dame"),
        ("University of Notre Dame", "notre-dame"),
        ("Purdue University", "purdue"),
    ],
)
def test_normalize_school(raw, expected):
    assert normalize_school(raw) == expected


def test_unknown_school_fails_instead_of_guessing():
    with pytest.raises(ValueError, match="Indiana State"):
        normalize_school("Indiana State University")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("(812) 555-0101", "812-555-0101"),
        ("812.555.0177", "812-555-0177"),
        ("765 555 0133", "765-555-0133"),
        ("+1 765 555 0133", "765-555-0133"),
        ("Not listed", None),
        ("ext 42", "ext 42"),
        (None, None),
    ],
)
def test_normalize_phone(raw, expected):
    assert normalize_phone(raw) == expected


def test_name_key_ignores_case_and_punctuation():
    assert name_key("Casey O'Neil") == name_key("casey oneil") == "casey oneil"


def record(school, name, title="Coach", email=None, phone=None, staff_id=None):
    return build_record(
        school=school,
        name=name,
        title=title,
        email=email,
        phone=phone,
        source_provider="test",
        source_url=None,
        staff_id=staff_id,
    )


def test_validation_flags_duplicates_and_missing_email():
    errors, warnings = validate_records(
        [
            record("Purdue", "A", email="a@purdue.edu"),
            record("Purdue", "B", email="a@purdue.edu"),
            record("Purdue", "C"),
        ]
    )
    assert errors == ["purdue/B: duplicate email 'a@purdue.edu' at the same school"]
    assert warnings == ["purdue/C: no email, identity can only be matched by name"]


def report_for(previous, current):
    with closing(sqlite3.connect(":memory:")) as con:
        build_database(con, previous, current)
        report = change_report(con)
    report = report.astype(object).where(report.notna(), None)
    return {row.name: (row.change_type, row.confidence) for row in report.itertuples()}


def test_exercise_data_produces_expected_changes():
    current, report = run()
    assert len(current) == 6
    changes = {row.name: row.change_type for row in report.itertuples()}
    assert changes == {
        "Taylor Morgan": "position_change",
        "Alex Johnson": "unchanged",
        "Sam Patel": "position_change",
        "Jordan Lee": "likely_transfer",
        "Avery Brooks": "departure",
        "Riley Chen": "addition",
        "Casey O'Neil": "addition",
    }


def test_every_record_is_accounted_for():
    current, report = run()
    assert set(report["staff_id"].dropna()) == {f"staff_00{i}" for i in range(1, 6)}
    current_rows = report[report["curr_school_id"].notna()]
    assert sorted(current_rows["name"]) == sorted(r.name for r in current)


def test_school_missing_from_scrape_is_not_a_departure():
    previous = [record("Purdue", "Pat Doe", staff_id="s1")]
    current = [record("Indiana", "Someone Else", email="se@iu.edu")]
    assert report_for(previous, current)["Pat Doe"] == ("status_unknown", None)


def test_name_only_transfer_is_low_confidence_and_not_merged():
    previous = [record("Purdue", "Pat Doe", email="pd@purdue.edu", staff_id="s1")]
    current = [
        record("Indiana", "Pat Doe", email="patricia@iu.edu"),
        record("Purdue", "Someone Else", email="se@purdue.edu"),
    ]
    with closing(sqlite3.connect(":memory:")) as con:
        build_database(con, previous, current)
        types = sorted(change_report(con)["change_type"])
    assert types == ["addition", "addition", "departure", "possible_transfer"]


def test_same_school_name_match_when_email_changes():
    previous = [record("Purdue", "Pat Doe", email="old@purdue.edu", staff_id="s1")]
    current = [record("Purdue", "Pat Doe", email="new@purdue.edu")]
    assert report_for(previous, current)["Pat Doe"] == ("unchanged", "medium")
