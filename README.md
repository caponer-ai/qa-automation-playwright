# QA automation with Playwright + pytest

[![tests](https://github.com/caponer-ai/qa-automation-playwright/actions/workflows/tests.yml/badge.svg)](https://github.com/caponer-ai/qa-automation-playwright/actions/workflows/tests.yml)

UI, API and scraper automation on public practice sites. The UI suite runs the same journeys for every
saucedemo account and detects the site's 12 intentional defects; each is documented with repro steps in
[BUGS.md](BUGS.md). Why things are built this way, and what each choice costs: [docs/decisions.md](docs/decisions.md).

| Suite | Target | What is covered |
|---|---|---|
| `ui` | [saucedemo.com](https://www.saucedemo.com) | login rules, catalogue, sorting, cart, checkout items, tax and total, form validation; a journey × account matrix |
| `api` | [restful-booker](https://restful-booker.herokuapp.com) | booking CRUD through a typed client, token auth, 403 without a token, 404 after delete |
| `scraper` | [books.toscrape.com](https://books.toscrape.com) | catalogue scraper with pagination and CSV/JSON export; parser tested offline on a recorded HAR and on edge-case markup, plus one live smoke test |

## How known defects are handled

Every matrix test has preconditions (plain asserts) and one narrow symptom check:

```python
def test_remove_from_cart(login_as, user, defects):
    inventory = login_as(user)
    slug = SLUGS[BACKPACK]
    inventory.add_to_cart(slug)
    expect(inventory.cart_badge).to_have_text("1")  # precondition: red on failure

    inventory.remove_from_cart(slug)

    with defects.symptom("remove_from_cart"):  # only this block can match a known bug
        expect(inventory.add_button(slug)).to_be_visible()
        expect(inventory.cart_badge).to_be_hidden()
```

`tests/ui/known_defects.py` maps `(user, symptom)` to a bug id. A registered symptom that fails is xfail;
one that passes turns red ("no longer reproduces"); a failure outside the block is red. A different failure
*inside* the block would still be filed under the known bug, so each block checks one field or element.
These rules have their own browser-free tests in `tests/ui/test_known_defects.py`, run in the CI lint job. Decision 5 explains why an earlier, simpler
approach (`xfail(raises=AssertionError)`) was replaced.

## Layout

```
pages/          Page Objects: locators and actions, no assertions
clients/        typed API client: Booking dataclasses, TransientHTTPError for 5xx
scraper/        books.toscrape.com scraper, also a CLI
settings.py     target URLs (overridable by env vars) and test accounts
tests/ui        login, inventory, checkout, user matrix, defect registry and its tests
tests/api       booking API
tests/scraper   offline parser tests, edge cases, HAR fixture and its recorder, live smoke test
docs/           design decisions
```

## Run

```bash
pip install -r requirements-dev.txt
playwright install chromium

pytest -n 4 -m "not perf"        # everything except timing checks, 4 workers
pytest -m perf -p no:xdist       # timing checks, one process
pytest -m ui                     # one suite: ui | api | scraper | unit | live | perf
pytest -m ui --headed            # watch the browser
pytest -rxX                      # list known defects in the summary

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

- Parallel run with pytest-xdist: the 128 tests outside `perf` take about 77 s on 4 workers instead of about
  267 s in one process (local Windows machine, 22.10.2026, 3 parallel runs and 1 sequential run).
- Login through the form at most once per account per worker, then the session cookie is reused (decision 2).
- Web-first `expect()` assertions wait for state; no `sleep` anywhere.
- Scraper tests replay a HAR with every other request blocked: no network, same input each run (decision 7).
- Reruns only for `TransientHTTPError`, timeouts and connection resets on the shared API, never for UI tests (decision 6).

## When a test fails

For tests on pytest-playwright's `page` fixture a screenshot and a trace are saved to `test-results/`;
the suite jobs in CI upload them as an artifact. Contexts created by hand (cached login, HAR replay) are not traced.
Open a trace with `playwright show-trace test-results/<test>/trace.zip` to step through every action,
network call and DOM snapshot.

## CI

GitHub Actions: `ruff`, `ruff format`, strict `mypy` on library code and the defect registry, and the browser-free
`unit` tests; every test must carry a suite marker or collection fails. Then the
`ui`, `api` and offline `scraper` suites in parallel; a Docker job that builds the image and runs the offline
suite inside it; and a non-blocking `signals` job for timing checks and the live scraper smoke test
(decisions 6 and 9). A weekly scheduled run catches changes on the third-party sites.
