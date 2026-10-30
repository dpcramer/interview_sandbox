"""One reader per website provider. Each maps its own field names onto StaffRecord."""

import csv
import json
from html.parser import HTMLParser
from pathlib import Path

from interview_sandbox.benchmark_staff.normalize import StaffRecord, build_record


def read_sidearm(path: Path) -> list[StaffRecord]:
    data = json.loads(path.read_text())
    school = data["school"]
    return [
        build_record(
            school=school["name"],
            name=person["full_name"],
            title=person.get("job_title"),
            email=person.get("email_address"),
            phone=person.get("telephone"),
            source_provider="sidearm",
            source_url=school.get("url"),
        )
        for person in data["staff"]
    ]


def read_wmt(path: Path) -> list[StaffRecord]:
    with path.open(newline="") as f:
        return [
            build_record(
                school=row["institution"],
                name=row["profile_name"],
                title=row.get("position") or None,
                email=row.get("email") or None,
                phone=row.get("phone") or None,
                source_provider="wmt",
                source_url=row.get("profile_url") or None,
            )
            for row in csv.DictReader(f)
        ]


class _StaffCardParser(HTMLParser):
    """Collects <section class="staff-card"> blocks under <main data-school="...">."""

    def __init__(self):
        super().__init__()
        self.school = None
        self.cards = []
        self._field = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = (attrs.get("class") or "").split()
        if tag == "main" and "data-school" in attrs:
            self.school = attrs["data-school"]
        elif tag == "section" and "staff-card" in classes:
            self.cards.append({})
        elif self.cards:
            if tag == "h2":
                self._field = "name"
            elif "role" in classes:
                self._field = "title"
            elif "email" in classes:
                self._field = "email"
            elif "phone" in classes:
                self._field = "phone"

    def handle_endtag(self, tag):
        self._field = None

    def handle_data(self, data):
        if self._field:
            card = self.cards[-1]
            card[self._field] = card.get(self._field, "") + data


def read_custom_html(path: Path, source_url: str | None = None) -> list[StaffRecord]:
    parser = _StaffCardParser()
    parser.feed(path.read_text())
    if parser.school is None:
        raise ValueError(f"{path}: no data-school attribute found")
    return [
        build_record(
            school=parser.school,
            name=card["name"],
            title=card.get("title"),
            email=card.get("email"),
            phone=card.get("phone"),
            source_provider="custom",
            source_url=source_url,
        )
        for card in parser.cards
    ]


def read_previous_snapshot(path: Path) -> list[StaffRecord]:
    return [
        build_record(
            school=row["school_name"],
            name=row["name"],
            title=row.get("title"),
            email=row.get("email"),
            phone=row.get("phone"),
            source_provider="previous_snapshot",
            source_url=row.get("source_url"),
            staff_id=row["staff_id"],
        )
        for row in json.loads(path.read_text())
    ]
