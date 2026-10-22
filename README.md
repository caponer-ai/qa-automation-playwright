# QA automation with Playwright + pytest

[![tests](https://github.com/caponer-ai/qa-automation-playwright/actions/workflows/tests.yml/badge.svg)](https://github.com/caponer-ai/qa-automation-playwright/actions/workflows/tests.yml)

UI, API and scraper automation on public practice sites. The UI suite runs the same journeys for every
saucedemo account and has found **12 defects**, each with repro steps in [BUGS.md](BUGS.md).
Why things are built this way: [docs/decisions.md](docs/decisions.md).

| Suite | Target | What is covered |
|---|---|---|
| `ui` | [saucedemo.com](https://www.saucedemo.com) | login rules, catalogue, sorting, cart, checkout totals, form validation; a journey × account matrix that finds defects |
| `api` | [restful-booker](https://restful-booker.herokuapp.com) | booking CRUD through a typed client, token auth, 403 without a token, 404 after delete |
| `scraper` | [books.toscrape.com](https://books.toscrape.com) | catalogue scraper with pagination, CSV/JSON export, tested offline on a recorded HAR plus one live smoke test |

## How it finds bugs

`tests/ui/test_user_matrix.py` runs eight journeys for each account that can log in. `standard_user` defines
correct behaviour. Confirmed defects are registered in one place:

```python
# tests/ui/known_defects.py
(User.PROBLEM, "checkout_form"): "BUG-09 typing Last Name overwrites First Name",
(User.ERROR, "complete_order"): "BUG-11 Finish does not complete the order",
```

Matching tests become `xfail(strict=True, raises=AssertionError)`. The suite stays green while a bug exists,
turns red when the bug is fixed, and stays red on timeouts or crashes, so an infrastructure problem is
never counted as a known bug.

## Layout

```
pages/          Page Objects: locators and actions, no assertions
clients/        typed API client (Booking dataclasses over APIRequestContext)
scraper/        books.toscrape.com scraper, also a CLI
settings.py     target URLs (overridable by env vars) and test accounts
tests/ui        login, inventory, checkout, user matrix, defect registry
tests/api       booking API
tests/scraper   offline parser tests, HAR fixture and its recorder, live smoke test
docs/           design decisions
```

## Run

```bash
pip install -r requirements-dev.txt
playwright install chromium

pytest -n 4                  # everything, 4 workers
pytest -m ui                 # one suite: ui | api | scraper | live
pytest -m ui --headed        # watch the browser
pytest -rxX                  # list known defects in the summary

python -m scraper.books --pages 5 --out books.csv
python -m tests.scraper.record_har     # re-record the HAR after the site changes
```

Docker (official Playwright image, non-root user):

```bash
docker build -t qa-automation .
docker run --rm qa-automation
```

Point the suite at another stand: `SHOP_URL=https://staging.example.com pytest -m ui`.

## Speed and stability

- Parallel run with pytest-xdist: 70 tests take about 42 s on 4 workers instead of about 133 s in one process
  (local Windows machine, 22.10.2026, 3 parallel and 2 sequential runs).
- Login through the form once per worker, then the session cookie is reused (decision 2).
- Web-first `expect()` assertions wait for state; no `sleep` anywhere.
- Scraper tests replay a HAR with every other request blocked: no network, same input each run (decision 7).
- Reruns only for transient network errors on the shared API, never for UI tests (decision 6).

## When a test fails

A screenshot and a Playwright trace are saved to `test-results/`; CI uploads them as an artifact.
Open a trace with `playwright show-trace test-results/<test>/trace.zip` to step through every action,
network call and DOM snapshot.

## CI

GitHub Actions: `ruff` + `ruff format` + strict `mypy` first, then the three suites in parallel, and a job
that builds the Docker image and runs the suite inside it. A weekly scheduled run catches changes on the
third-party sites.
