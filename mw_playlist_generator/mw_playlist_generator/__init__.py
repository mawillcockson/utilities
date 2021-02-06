# mypy: allow-untyped-calls
"""
This file causes python to treat the folder it's in as a package.

It's also used to find the version string.
"""
import sys
from typing import cast

# From:
# https://github.com/mawillcockson/eggord/blob/ea7e56ce173561a550a08b67a9dafdaec149ff17/eggord/__init__.py
# pylint: disable=no-name-in-module, disable=import-error
if sys.version_info >= (3, 8):
    from importlib.metadata import version as metadata_version
else:
    from importlib_metadata import version as metadata_version

__version__ = str(cast(str, metadata_version(__name__)))
