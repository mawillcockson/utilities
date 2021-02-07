"""
custom types used by other modules
"""
from abc import ABC, abstractmethod
from argparse import ArgumentTypeError
from pathlib import Path
from typing import (  # pylint: disable=unused-import
    Dict,
    Iterable,
    List,
    Type,
    Union,
    cast,
)

from .logging import log

PostProcessors = List[Dict[str, str]]
PathType = Union[str, Path]


class ConfigError(ValueError):
    "a custom configuration error type"


class ArgumentValidationError(ArgumentTypeError, TypeError):
    "subclasses both argparse.ArgumentTypeError and TypeError"


class StrictPath(ABC):
    """
    a base class meant to be the left-most class in the list of classes a
    deriving class subclasses

    the current implementation for this doesn't make any methods of deriving
    classes available on instances

    for that, bind the methods in the class namespace to the Path() instance
    created in __new__()

    see:
    https://stackoverflow.com/a/1015405
    """

    def __new__(cls, value: PathType) -> "StrictPath":
        # pylint: disable=arguments-differ
        "create a new instance of pathlib.Path with stricter requirements"
        return cast(StrictPath, cls._check(value))

    @classmethod
    def __get_validators__(
        cls,
    ) -> "Iterable[Type[StrictPath]]":
        "enables pydantic to use this as a custom type"
        yield cls

    @staticmethod
    @abstractmethod
    def _check(value: PathType) -> Path:
        """
        performs extra checks

        must return an object of type pathlib.Path
        """
        raise NotImplementedError("the deriving class must override this")


class OpenablePath(StrictPath, Path):
    "Will only take a file that's able to be read"

    @staticmethod
    def _check(value: PathType) -> Path:
        "checks that the filename is a valid path, and returns it"
        if not value:
            message = "must pass a filename"
            log.exception(message)
            raise ArgumentValidationError(message)

        path = Path(value).resolve()

        if not path.is_file():
            message = f"'{path}' is not a file"
            log.exception(message)
            raise ArgumentValidationError(message)

        try:
            with path.open(mode="rb") as file:
                file.read(0)
        except OSError as err:
            message = f"cannot open '{path}'"
            log.exception(message)
            raise ArgumentValidationError(message) from err

        return path


class Directory(StrictPath, Path):
    "A type that indicates a directory that exists and is writeable"

    @staticmethod
    def _check(value: PathType) -> Path:
        "checks that the folder name is a valid, writeable path, and returns it"
        if not value:
            message = "must pass a filename"
            log.exception(message)
            raise ArgumentValidationError(message)

        path = Path(value).resolve(strict=True)

        if not path.is_dir() and path.exists():
            message = f"'{path}' is not a directory"
            log.exception(message)
            raise ArgumentValidationError(message)

        try:
            path.mkdir(exist_ok=True)
        except OSError as err:
            message = (
                f"cannot create '{path}'; may not have permission\n"
                f"does '{path.parent}' exist?"
            )
            log.exception(message)
            raise ArgumentValidationError(message) from err

        log.debug("directory exists: '%s'", path)

        temporary_file = path / f"{__name__}.temporary_file"
        assert not temporary_file.exists(), f"'{temporary_file}' must not already exist"
        try:
            temporary_file.touch()
        except OSError as err:
            message = "Cannot create '{temporary_file}' in '{path}'"
            log.exception(message)
            raise ArgumentValidationError(message) from err

        log.debug("removing temporary file '%s'", temporary_file)
        temporary_file.unlink()

        return path
