"""
This file causes python to treat the folder it's in as a package.

It's also used to find the version string.
"""
import sys

# From:
# https://github.com/mawillcockson/eggord/blob/ea7e56ce173561a550a08b67a9dafdaec149ff17/eggord/__init__.py
if sys.version_info >= (3, 8):
    from importlib.metadata import version as metadata_version
else:
    # isort: off
    from importlib_metadata import (  # pylint: disable=import-error
        version as metadata_version,
    )

    # isort: on

__version__ = str(metadata_version(__name__))
