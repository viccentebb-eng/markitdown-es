import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from markitdown_es.__main__ import create_app


@pytest.fixture(scope="session")
def qapp():
    return create_app()
