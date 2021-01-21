from sstatic import __version__


def test_version():
    assert isinstance(
        __version__, str
    ), f"__version__ must be a str; it's a '{type(__version__)}'"

    assert __version__.isascii(), f"__version__ must be ascii: {__version__}"

    assert (
        __version__.count(".") == 2
    ), f"__version__ must be in semver format: {__version__}"

    assert all(
        section.isdigit() for section in __version__.split(".")
    ), f"all version sections must be integers: {__version__}"
