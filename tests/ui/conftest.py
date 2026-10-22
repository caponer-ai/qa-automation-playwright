import pytest

from tests.ui.known_defects import KNOWN_DEFECTS


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "check(name): scenario name used to look up KNOWN_DEFECTS")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Marks (user, check) pairs from the defect registry as expected failures."""
    for item in items:
        check = item.get_closest_marker("check")
        callspec = getattr(item, "callspec", None)
        if check is None or callspec is None or "user" not in callspec.params:
            continue
        reason = KNOWN_DEFECTS.get((callspec.params["user"], check.args[0]))
        if reason:
            # raises=AssertionError: a timeout or crash is still a red test, not a "known bug"
            item.add_marker(pytest.mark.xfail(reason=reason, strict=True, raises=AssertionError))
