# interview_sandbox

Python sandbox for live-coding data engineering exercises.

- Virtual environment is `default_venv/` (not `.venv`). Activate with `source default_venv/bin/activate`.
- Use the Makefile: `make install`, `make test`, `make lint`, `make format`, `make run`, `make update`.
- Code lives in the `interview_sandbox/` package; tests live in `tests/`.
- Available libraries are in `requirements.in` (pandas, polars, pyarrow, duckdb, sqlalchemy, requests, faker). When a new library would make a solution better (e.g. Faker for mock data), ask before adding it instead of assuming the answer is no and working around it. To add one, put it in `requirements.in` and run `make update`; never edit `requirements.txt` by hand.
- Add a test in `tests/` for any new function, and run `make test` and `make lint` before saying something works.
- Keep solutions simple and readable; explain trade-offs briefly.
