# Benchmark staff pipeline

The exercise brief is in [EXERCISE.md](EXERCISE.md). The source files are in [inputs/](inputs/).

## Run it

```bash
make staff-report    # or: default_venv/bin/python -m interview_sandbox.benchmark_staff.pipeline
make test
```

Outputs:

- [output/normalized_current.json](output/normalized_current.json): the normalized current records
- [output/change_report.csv](output/change_report.csv): every person, classified
- `data/benchmark_staff.db`: the SQLite database, so the SQL can be explored by hand (`sqlite3 data/benchmark_staff.db`)

## Layout

| File | What it does |
| --- | --- |
| `sources.py` | One reader per provider (Sidearm JSON, WMT CSV, custom HTML, previous snapshot) mapping its fields onto `StaffRecord` |
| `normalize.py` | School aliases, title, phone, email, name-key rules and `validate_records` |
| `sql/schema.sql` | SQLite tables |
| `sql/change_report.sql` | The comparison, all in SQL |
| `pipeline.py` | Read, validate, load SQLite, run the report |

## Result

| change | confidence | who | detail |
| --- | --- | --- | --- |
| position_change | high | Taylor Morgan, Indiana | Assistant AD, Compliance → Associate AD, Compliance |
| position_change | high | Sam Patel, Purdue | Sports Dietitian → Sports Nutritionist |
| likely_transfer | medium | Jordan Lee, Purdue → Notre Dame | same name, same phone, same email username (jlee@) |
| departure | medium | Avery Brooks, Purdue | not on the current Purdue page |
| addition | high | Casey O'Neil, Purdue | |
| addition | medium | Riley Chen, Indiana | no email, so identity cannot be confirmed |
| unchanged | high | Alex Johnson, Notre Dame | "Dir., Football Operations" normalizes to match "Director of Football Operations" |

## Modeling

- **`staff_observations`** is the core table. It is append-only, with one row per person per snapshot, and it keeps the raw title next to the normalized one. Facts never change. If the normalization rules improve, history can be reprocessed.
- **`snapshots`** and **`snapshot_coverage`** record which schools each scrape reached. Someone counts as a departure only if their school was scraped successfully. If the scrape failed, they come out as `status_unknown`. Without this, one broken scrape would look like a whole department leaving.
- **`schools`** holds the canonical school list. Aliases are an explicit map in code, not fuzzy matching. An unknown name raises an error rather than being guessed, so "Indiana State" can never merge into Indiana.

## Matching, and how uncertainty is kept

1. **Same school:** match on email first, then on exact normalized name. Each record can be used once, and an email match beats a name match. Email matches are `high` confidence; name matches are `medium`.
2. **Different school:** match unmatched leftovers by name. The link is a `likely_transfer` (`medium`) only if a contact detail backs it up: same phone, same email, or same email username. A name alone gives a `possible_transfer` (`low`). Low-confidence links are reported but **not merged**: the person still also appears as a departure and an addition.
3. **Departures** are `medium` because one missing scrape could just be noise.
4. **Title synonyms** are not merged. "Dietitian" vs "Nutritionist" shows up as a position change. Whether those are the same job is a business decision, and it belongs in a reviewed synonym table, not in a regex.

## How this holds weekly history

Each weekly run inserts one `snapshots` row, its coverage rows, and its observations. On top of that:

- **`staff`** (`staff_id`, canonical name): the person.
- **`staff_identity_links`** (`observation_id`, `staff_id`, `match_basis`, `confidence`, `decided_by` rule/human, `decided_at`): matches stored as data. They can be audited, a reviewer can override them, and they can be undone without rewriting observations. Low-confidence candidates go to a review queue.
- **`staff_positions`** (SCD type 2: `staff_id`, `school_id`, `title`, `valid_from`, `valid_to`): derived from observations plus links. A row opens on the first snapshot where it appears. It closes only after N consecutive covered snapshots without it, which absorbs scrape flakiness.

Each week's change report is then the same SQL run against "last snapshot vs this snapshot". It could also run against the current `staff_positions` state, so people who were missing for one week are not flagged again.

## Next steps

- Make the one-to-one matching strict when names collide inside a school. The `row_number()` dedupe is greedy, which is fine at this size.
- Report contact changes (new phone or email) as their own change type.
- Add a reviewed title-synonym table and a canonical role taxonomy (role level + department) for analytics.
- Add data-quality metrics per scrape (row count change vs the last run, % missing email), and alert when a page shrinks suddenly.
- Add one reader module per provider version, with fixture tests against saved pages.
