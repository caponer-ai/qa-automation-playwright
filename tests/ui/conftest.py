import pytest

from settings import User
from tests.ui.known_defects import Defects


@pytest.fixture
def defects(user: User) -> Defects:
    return Defects(user)
