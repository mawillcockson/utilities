"""
custom types used by other modules
"""
from abc import ABC, abstractmethod
from argparse import ArgumentTypeError
from pathlib import Path
from typing import Dict, Iterable, List, Type, Union  # pylint: disable=unused-import

from .logging import log

PostProcessors = List[Dict[str, str]]


class ConfigError(ValueError):
    "a custom configuration error type"


class ArgumentValidationError(ArgumentTypeError, TypeError):
    "subclasses both argparse.ArgumentTypeError and TypeError"


class StrictPath(ABC):
    "defines methods common to OpenablePath and Directory"

    def __init__(self, filename: "Union[str, Path, None, StrictPath]" = None):
        "runs the check"
        self.path = self._check(str(filename))

    @property
    def stem(self) -> str:
        "the final path component, minus its last suffix"
        return self.path.stem

    def read_text(self) -> str:
        "open the file in text mode, read it, and close the file"
        return self.path.read_text()

    def write_text(self, text: str) -> None:
        "open the file in text mode, write to it, and close the file"
        self.path.write_text(text)

    def __truediv__(self, path: "Union[str, Path, StrictPath]") -> Path:
        "combine paths"
        if isinstance(path, StrictPath):
            return self.path / str(path)

        return self.path / path

    def is_dir(self) -> bool:
        "checks if the path is a directory"
        return self.path.is_dir()

    def is_file(self) -> bool:
        "checks if the path is a file"
        return self.path.is_file()

    def glob(self, pattern: str) -> Iterable[Path]:
        """
        iterate over this subtree and yield all existing files (of any kind,
        including directories) matching the given relative pattern
        """
        yield from self.path.glob(pattern)

    @property
    def parent(self) -> Path:
        "the logical parent of the path"
        return self.path.parent

    def __str__(self) -> str:
        """
        return the string representation of the path, suitable for passing to
        system calls
        """
        return str(self.path)

    @abstractmethod
    @staticmethod
    def _check(filename: Union[str, Path, None] = None) -> Path:
        "the method that implements the custom check behaviour"
        raise NotImplementedError(
            "This method must be implemented in the deriving class"
        )

    @classmethod
    def __get_validators__(
        cls,
    ) -> "Iterable[Type[StrictPath]]":
        "enables pydantic to use this as a custom type"
        yield cls


class OpenablePath(StrictPath):
    "Will only take a file that's able to be read"

    @staticmethod
    def _check(filename: Union[str, Path, None] = None) -> Path:
        "checks that the filename is a valid path, and returns it"
        if not filename:
            message = "must pass a filename"
            log.exception(message)
            raise ArgumentValidationError(message)

        path = Path(filename).resolve()

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


class Directory(StrictPath):
    "A type that indicates a directory that exists and is writeable"

    @staticmethod
    def _check(filename: Union[str, Path, None] = None) -> Path:
        "checks that the folder name is a valid, writeable path, and returns it"
        if not filename:
            path = Path().resolve(strict=False)
        else:
            path = Path(filename).resolve(strict=False)

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
