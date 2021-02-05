"""
utility functions not specific to any module
"""
from functools import partial
from pathlib import Path
from pprint import pformat
from typing import Iterable, Union

from .logging import log
from .types import OpenablePath

pretty = partial(pformat, indent=2, compact=False)


def filter_inaccessible(files: Iterable[Union[str, Path]]) -> Iterable[OpenablePath]:
    "removes files that don't exist anymore"
    for file in files:
        try:
            path = OpenablePath(file)
        except TypeError:
            log.debug("filtered '%s'", file)

        yield path
