"""
tests for the version string only
"""
import re

from mw_playlist_generator import __version__

semver_re = re.compile(r"^(\d+\.){2}\d+$")


def test_version() -> None:
    "make sure the version is a string that matches semver format"
    assert isinstance(
        __version__, str
    ), f"__version__ must be a str, not '{type(__version__)}'"
    assert semver_re.match(
        __version__
    ), f"'{__version__}' is not in simple semver.org format"
