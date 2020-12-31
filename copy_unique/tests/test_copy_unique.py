"""
the tests for the main app functionality
"""
from copy_unique import __version__


def test_version() -> None:
    "is __version__ a 5-character string"
    assert isinstance(__version__, str)
    assert len(__version__) == 5
