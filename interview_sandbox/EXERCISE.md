# Benchmark Staff Pipeline Exercise

## Context

Benchmark maintains current and historical staff records for college athletic departments. Staff directories come from several website providers and use inconsistent formats and titles.

You have been given:

- `previous_snapshot.json`: the previously normalized staff records.
- `sidearm_current.json`: a current Sidearm-style source.
- `wmt_current.csv`: a current WMT-style source.
- `custom_current.html`: a current custom website source.

## Your task

Build a small pipeline that:

1. Reads the three current source files.
2. Produces one common staff-record format.
3. Normalizes obvious variations in school names and job titles.
4. Loads the previous snapshot and the normalized current records into a local SQL database (DuckDB or SQLite is fine).
5. Uses SQL to compare the current records with `previous_snapshot.json`.
6. Reports additions, departures, position changes, and likely school transfers.
7. Includes a few useful tests or validation checks.

Be ready to explain how you modeled the tables and how this design would hold staff history over many weekly scrapes.

An output record might contain:

```json
{
  "school_id": "indiana",
  "name": "Taylor Morgan",
  "title": "Associate Athletic Director, Compliance",
  "email": "tmorgan@iu.edu",
  "phone": "812-555-0101",
  "source_url": "https://example.edu/staff"
}
```

You may choose a different schema if you can explain why.

## Expectations

- Use any programming language, libraries, and AI tools you normally use.
- You do not need to build a production-complete system.
- Prioritize a sensible working slice.
- Preserve uncertainty rather than forcing unsafe identity matches.
- Be prepared to explain your approach, tradeoffs, AI usage, validation, and next steps.

## Deliverables

- Runnable code or a clear executable prototype.
- Normalized current records.
- A change report, plus the SQL that produces it.
- Tests or validation checks.
- A short README or notes explaining how to run it and what you would improve next.
