"""
utility functions not specific to any module
"""
from functools import partial
from pathlib import Path
from pprint import pformat
from typing import Iterable, Union

from .logging import log

pretty = partial(pformat, indent=2, compact=False)


def filter_inaccessible(files: Iterable[Union[str, Path]]) -> Iterable[Path]:
    "removes files that don't exist anymore"
    for file in files:
        try:
            path = Path(file).resolve(strict=True)
            with path.open() as temporary_file:
                temporary_file.read(0)
            yield path
        except OSError:
            log.debug("filtered '%s'", file)
