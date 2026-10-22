"""The defect registry and the symptom() rules, tested without a browser."""

import pytest

from settings import ACTIVE_USERS, User
from tests.ui.known_defects import KNOWN_DEFECTS, SYMPTOMS, Defects


def test_registry_uses_known_symptoms():
    assert {symptom for _, symptom in KNOWN_DEFECTS} <= SYMPTOMS


def test_registry_uses_matrix_users():
    assert {user for user, _ in KNOWN_DEFECTS} <= set(ACTIVE_USERS)


def test_every_entry_has_a_bug_id():
    assert all(reason.startswith("BUG-") for reason in KNOWN_DEFECTS.values())


# --- behaviour of defects.symptom() -------------------------------------
# (User.PROBLEM, "product_link") is registered, (User.STANDARD, "product_link") is not.


def test_registered_symptom_that_fails_is_xfail():
    with pytest.raises(pytest.xfail.Exception, match="BUG-08"), Defects(User.PROBLEM).symptom("product_link"):
        raise AssertionError("opened the wrong product")


def test_registered_symptom_that_passes_is_red():
    with (
        pytest.raises(pytest.fail.Exception, match="no longer reproduces"),
        Defects(User.PROBLEM).symptom("product_link"),
    ):
        pass


def test_unregistered_failure_stays_red():
    with pytest.raises(AssertionError), Defects(User.STANDARD).symptom("product_link"):
        raise AssertionError("new regression")


def test_non_assertion_error_is_never_a_known_defect():
    with pytest.raises(TimeoutError), Defects(User.PROBLEM).symptom("product_link"):
        raise TimeoutError("page did not load")


def test_unknown_symptom_name_is_rejected():
    with pytest.raises(AssertionError, match="unknown symptom"), Defects(User.PROBLEM).symptom("typo"):
        pass
