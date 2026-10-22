# Defects detected by the suite

saucedemo ships these accounts with intentional, publicly known defects, so this is not a discovery.
What it shows is the method: run the same journeys for every account, treat `standard_user` as the
reference, confirm each difference by hand, then register it. The defects were first spotted with an
exploratory script and are now checked by `tests/ui/test_user_matrix.py`.

Each defect is registered in `tests/ui/known_defects.py` against one narrow symptom check
(`defects.symptom(...)`, see docs/decisions.md, decision 5). The test is xfail while the defect reproduces,
red when it stops reproducing, and red for any failure outside the symptom block.

Common precondition: open https://www.saucedemo.com, log in with the listed user and password `secret_sauce`.

| ID | Account | Severity | Summary |
|---|---|---|---|
| BUG-01 | problem_user | Major | Every product shows the same "404" image |
| BUG-02 | visual_user | Minor | Backpack shows the "404" image |
| BUG-03 | visual_user | Critical | Catalog prices differ from the real prices |
| BUG-04 | problem_user, error_user | Major | Sorting does nothing |
| BUG-05 | visual_user | Major | Sort "Price (low to high)" returns an unsorted list |
| BUG-06 | problem_user, error_user | Critical | 3 of 6 products cannot be added to the cart |
| BUG-07 | problem_user, error_user | Major | "Remove" on the catalog page does nothing |
| BUG-08 | problem_user | Major | Product name opens a different product |
| BUG-09 | problem_user | Critical | Typing Last Name overwrites First Name, checkout is blocked |
| BUG-10 | error_user | Major | Last Name ignores input, form is accepted anyway |
| BUG-11 | error_user | Critical | "Finish" does not complete the order |
| BUG-12 | performance_glitch_user | Major | Login takes about 5 s |

## Details

**BUG-01** · problem_user
1. Look at the product images on the catalog page.
- Expected: six different product photos.
- Actual: all six `img` elements point to the same placeholder `sl-404-*.jpg`.

**BUG-02** · visual_user
1. Look at the Sauce Labs Backpack image.
- Expected: backpack photo.
- Actual: `sl-404-*.jpg` placeholder. Other products are fine.

**BUG-03** · visual_user
1. Compare catalog prices with standard_user (Backpack $29.99, Bike Light $9.99, ...).
- Expected: same prices for every account.
- Actual: different prices, for example Backpack $61.63. Whether checkout charges the catalog price or the real one was not checked.

**BUG-04** · problem_user, error_user
1. Choose "Name (Z to A)" or "Price (low to high)" in the sort dropdown.
- Expected: list re-ordered.
- Actual: order unchanged. error_user also gets a browser alert "Sorting is broken! This error has been reported to Backtrace."

**BUG-05** · visual_user
1. Choose "Price (low to high)".
- Expected: prices ascending.
- Actual: prices not in ascending order (observed: $11.36, $21.22, $99.6, $99.56, $16.96, $18.03).

**BUG-06** · problem_user, error_user
1. Click "Add to cart" on each of the six products.
- Expected: every button turns into "Remove", badge shows 6.
- Actual: Bolt T-Shirt, Fleece Jacket and Test.allTheThings() T-Shirt (Red) stay "Add to cart". No error is shown.

**BUG-07** · problem_user, error_user
1. Add Sauce Labs Backpack, then click "Remove" on the catalog page.
- Expected: button back to "Add to cart", badge cleared.
- Actual: nothing changes.

**BUG-08** · problem_user
1. Click the "Sauce Labs Backpack" title.
- Expected: Backpack product page.
- Actual: opens `inventory-item.html?id=5`, the Fleece Jacket page.

**BUG-09** · problem_user
1. Add any product, go to Cart, click Checkout.
2. Type `Test` in First Name, then `User` in Last Name.
- Expected: First Name `Test`, Last Name `User`.
- Actual: First Name becomes `User`, Last Name stays empty, Continue shows "Last Name is required". The order cannot be placed.

**BUG-10** · error_user
1. On checkout step one type into Last Name.
- Expected: text appears in the field.
- Actual: field stays empty, yet Continue accepts the form. Required-field validation is bypassed.
- Automated: the ignored input (`checkout_form`). That the form is then accepted was confirmed manually.

**BUG-11** · error_user
1. Complete checkout step one, click "Finish" on the overview.
- Expected: "Thank you for your order!" page.
- Actual: stays on the overview page. The customer believes they ordered, nothing happens.

**BUG-12** · performance_glitch_user
1. Submit the login form.
- Expected: catalog within the 3 s budget (standard_user: about 0.1 s).
- Actual: about 5.1 s (single local measurement, 22.10.2026).
