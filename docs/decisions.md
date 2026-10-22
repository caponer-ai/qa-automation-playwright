# Design decisions

Short records of the choices that shape this suite, with what each one costs.

## 1. Playwright, not Selenium

**Why:** built-in auto-waiting and web-first assertions remove most `sleep`-style flakiness; tracing gives a
step-by-step replay of a failed test; the same tool covers UI, HTTP API (`APIRequestContext`) and network
interception (HAR replay), so the suite has one dependency instead of three.

**Cost:** smaller ecosystem than Selenium, no Selenium Grid. For legacy browsers or an existing Grid,
Selenium would be the better fit.

## 2. Log in through the form once per worker, then reuse the session cookie

**Why:** a UI login in every test adds one page load and one more place to fail. Login behaviour is
covered by its own tests (`test_login.py`, `test_login_within_budget`); everything else starts logged in.

**Cost:** relies on saucedemo keeping the session in a cookie. If that changes, `session_cookies` in
`conftest.py` is the single place to update.

## 3. Locators by `data-test`, roles where there is no test id

**Why:** test ids survive layout and styling changes; CSS chains and XPath do not. The burger menu has no
test id, so it is found by its accessible role and name.

**Cost:** depends on developers keeping the attributes. In a real team this is an agreement with them,
not something the test code can enforce.

## 4. Page Objects hold locators and actions, tests hold assertions

**Why:** a reader sees what is checked without opening page classes; page classes stay reusable across
positive and negative tests.

**Cost:** a few more lines per test than "smart" page methods like `assert_cart_count()`.

## 5. Known defects: one registry, strict xfail limited to `AssertionError`

**Why:** the same journeys run for all six accounts. Confirmed bugs are listed once in
`tests/ui/known_defects.py`; the matching tests are expected to fail. `strict=True` turns a fixed bug into a
red test, so the registry cannot go stale. `raises=AssertionError` keeps timeouts and crashes red, so an
infrastructure problem is never mistaken for a known bug.

**Cost:** a different assertion failing in an already-xfailed test would be hidden. Mitigation: each
matrix test checks one behaviour.

## 6. Reruns only for transient network errors on the external API

**Why:** restful-booker is a shared public sandbox and occasionally times out. Reruns are limited to
timeouts, connection resets and 5xx. UI tests are never rerun: a flaky UI test is a bug in the test.

**Cost:** a real 5xx regression would be retried twice before failing, adding a few seconds.

## 7. Scraper tests replay a recorded HAR; one live smoke test checks the real site

**Why:** parsing logic is tested on fixed input with the network blocked, so failures mean the parser is
wrong, not that the site was slow. Blocking all other requests already caught one bug: the scraper loaded
one page more than asked.

**Cost:** the recording goes stale when the site changes. The live smoke test detects that, and
`python -m tests.scraper.record_har` re-records it.

## 8. Sync API

**Why:** pytest-playwright fixtures are sync, and test code reads top to bottom. Parallelism comes from
pytest-xdist processes.

**Cost:** a large scraping job would be faster on the async API with several pages per browser.

## Next steps if this suite grew

- HTML or Allure report published from CI.
- Unique test data per run on the shared API sandbox, since other users can reset or edit it.
- Visual comparison for `visual_user`, run only inside the pinned Docker image so fonts match.
- Splitting CI shards by recorded test duration once the suite takes minutes, not seconds.
