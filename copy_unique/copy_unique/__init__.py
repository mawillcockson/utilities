"""
the first file imported when the library is imported
"""
import sys
from typing import cast

# From:
# https://github.com/mawillcockson/eggord/blob/ea7e56ce173561a550a08b67a9dafdaec149ff17/eggord/__init__.py
# Don't want isort moving the pylint comments
# isort: off
if sys.version_info >= (3, 8):
    from importlib.metadata import (  # pylint: disable=no-name-in-module, import-error
        version as metadata_version,
    )

    def version(name: str) -> str:
        "returns the version of the current module"
        return metadata_version(name)


else:
    from importlib_metadata import (  # pylint: disable=import-error
        version as metadata_version,
    )

    def version(name: str) -> str:
        "returns the version of the current module"
        # NOTE:FUTURE the backport module doesn't define a return type, and
        # mypy detects Any
        return cast(str, metadata_version(name))


# isort: on


__version__ = version(name=__name__)
