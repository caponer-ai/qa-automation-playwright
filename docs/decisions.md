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
With `-n 4` that is at most one form login per account per worker.

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

## 5. Known defects: a registry plus an explicit symptom block

**Why:** the same journeys run for the five accounts that can log in (`locked_out_user` is covered by the
login tests). Each test has preconditions, written as plain asserts, and one check wrapped in
`defects.symptom(name)`. Only that block is looked up in `tests/ui/known_defects.py`:

- registered and failing: xfail with the bug id;
- registered and passing: red, "no longer reproduces", so the registry cannot go stale;
- not registered, or any failure outside the block (including an `expect()` timeout in a precondition): red.

An earlier version marked whole tests `xfail(raises=AssertionError)`. That was wrong: `expect()` also raises
`AssertionError` when its wait times out, so a new regression in a precondition was filed under an old bug.
The rules above are tested without a browser in `tests/ui/test_known_defects.py`.

**Cost:** one more concept for a reader, and the classification is only as precise as the block: a different
failure *inside* a symptom block is still filed under the known bug. Blocks are therefore kept to one field or
element: add-to-cart is checked per product, remove separately, and checkout fields one by one.

## 6. Reruns only for transient API errors; timing is a signal, not a gate

**Why:** restful-booker is a shared public sandbox. The client raises `TransientHTTPError` for any 5xx, and
only that, timeouts and connection resets are retried. Wrong answers fail at once. UI tests are never
rerun: a flaky UI test is a bug in the test.

The login time budget runs in a separate, non-blocking CI job without parallel workers: on shared runners
CPU contention and network to a third-party site move the number, and a red merge gate without a product
bug would teach people to ignore red.

**Cost:** a slow-login regression does not block a merge; someone has to look at the signals job.

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

## 9. What "offline" and "external" mean here

The UI and API suites test third-party demo sites; there is no application of our own to start locally,
so they are integration tests by nature and depend on those sites being up. Only the scraper parser
tests are fully offline. The Docker job runs exactly that offline set, so a third-party outage cannot
fail the image check.

## Next steps if this suite grew

- HTML or Allure report published from CI.
- Unique test data per run on the shared API sandbox, since other users can reset or edit it.
- Visual comparison for `visual_user`, run only inside the pinned Docker image so fonts match.
- Splitting CI shards by recorded test duration once the suite takes minutes, not seconds.
