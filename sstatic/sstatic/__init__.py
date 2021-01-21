import sys

# From:
# https://github.com/mawillcockson/eggord/blob/ea7e56ce173561a550a08b67a9dafdaec149ff17/eggord/__init__.py
if sys.version_info >= (3, 8):
    from importlib.metadata import version as metadata_version
else:
    from importlib_metadata import version as metadata_version

__version__ = str(metadata_version(__name__))
