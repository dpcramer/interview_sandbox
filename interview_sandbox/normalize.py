"""Normalization rules shared by every source, and the common staff record."""

import re
import unicodedata
from dataclasses import dataclass

# Canonical schools. Aliases are explicit rather than fuzzy so "Indiana State" can never
# silently collapse into "indiana"; an unknown name fails loudly and gets added here.
SCHOOLS = {
    "indiana": "Indiana University",
    "notre-dame": "University of Notre Dame",
    "purdue": "Purdue University",
}

SCHOOL_ALIASES = {
    "indiana": "indiana",
    "indiana university": "indiana",
    "iu": "indiana",
    "notre dame": "notre-dame",
    "university of notre dame": "notre-dame",
    "purdue": "purdue",
    "purdue university": "purdue",
}

TITLE_ABBREVIATIONS = [
    (r"\bAssoc\.", "Associate"),
    (r"\bAsst\.", "Assistant"),
    (r"\bDir\.", "Director"),
    (r"\bSr\.", "Senior"),
    (r"\bCoord\.", "Coordinator"),
    (r"\bAD\b", "Athletic Director"),
]

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]+$")
PHONE_PATTERN = re.compile(r"^\d{3}-\d{3}-\d{4}$")


@dataclass(frozen=True)
class StaffRecord:
    school_id: str
    name: str
    title: str | None
    title_raw: str | None
    email: str | None
    phone: str | None
    source_provider: str
    source_url: str | None
    staff_id: str | None = None

    @property
    def name_key(self) -> str:
        return name_key(self.name)


def normalize_school(raw: str) -> str:
    key = " ".join(re.sub(r"[^a-z ]", "", raw.lower()).split())
    try:
        return SCHOOL_ALIASES[key]
    except KeyError:
        raise ValueError(f"Unknown school name: {raw!r}") from None


def normalize_title(raw: str | None) -> str | None:
    """Expand abbreviations and use 'Role, Area' form: 'Assoc. AD / Compliance' ->
    'Associate Athletic Director, Compliance'. Synonyms (Dietitian vs Nutritionist) are
    deliberately left alone: whether they are the same job is a business decision."""
    if raw is None:
        return None
    title = " ".join(raw.split())
    for pattern, replacement in TITLE_ABBREVIATIONS:
        title = re.sub(pattern, replacement, title)
    title = title.replace("&", "and")
    title = re.sub(r"\s+[/|–—-]\s+", ", ", title)
    title = re.sub(r"\b(Director|Coordinator|Manager) of\b", r"\1,", title)
    title = re.sub(r"\s*,[\s,]*", ", ", title)
    return title.strip(" ,") or None


def normalize_email(raw: str | None) -> str | None:
    if raw is None:
        return None
    return raw.strip().lower() or None


def normalize_phone(raw: str | None) -> str | None:
    """Format US numbers as 812-555-0101. Text with no digits ('Not listed') becomes None;
    anything else unparseable is kept as-is so validation can flag it instead of losing it."""
    if raw is None:
        return None
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return None
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return raw.strip()
    return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"


def name_key(name: str) -> str:
    """Match key for names: 'Casey O'Neil' -> 'casey oneil'."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z ]", "", ascii_name.lower()).split())


def build_record(
    *,
    school: str,
    name: str,
    title: str | None,
    email: str | None,
    phone: str | None,
    source_provider: str,
    source_url: str | None,
    staff_id: str | None = None,
) -> StaffRecord:
    title_raw = " ".join(title.split()) if title else None
    return StaffRecord(
        school_id=normalize_school(school),
        name=" ".join(name.split()),
        title=normalize_title(title_raw),
        title_raw=title_raw,
        email=normalize_email(email),
        phone=normalize_phone(phone),
        source_provider=source_provider,
        source_url=source_url,
        staff_id=staff_id,
    )


def validate_records(records: list[StaffRecord]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Errors stop the load; warnings are reported."""
    errors, warnings = [], []
    seen_emails = set()
    for r in records:
        label = f"{r.school_id}/{r.name}"
        if not r.name:
            errors.append(f"{label}: missing name")
        if r.email is None:
            warnings.append(f"{label}: no email, identity can only be matched by name")
        elif not EMAIL_PATTERN.match(r.email):
            errors.append(f"{label}: malformed email {r.email!r}")
        elif (r.school_id, r.email) in seen_emails:
            errors.append(f"{label}: duplicate email {r.email!r} at the same school")
        else:
            seen_emails.add((r.school_id, r.email))
        if r.phone is not None and not PHONE_PATTERN.match(r.phone):
            warnings.append(f"{label}: unparseable phone {r.phone!r}")
        if r.title is None:
            warnings.append(f"{label}: no title")
    return errors, warnings
