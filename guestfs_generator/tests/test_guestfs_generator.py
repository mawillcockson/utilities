"""
main tests for guestfs_generator
"""
import re

from guestfs_generator import __version__

semver_re = re.compile(r"^(\d+\.){2}\d+$")


def test_version() -> None:
    "make sure the version matches semver format, and is a string"
    assert isinstance(
        __version__, str
    ), f"__version__ must be a str, not '{type(__version__)}'"
    assert semver_re.match(
        __version__
    ), f"'{__version__}' is not in simple semver.org format"
