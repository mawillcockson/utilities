"""
custom types used by other modules
"""
from argparse import ArgumentTypeError
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Union

from .logging import log

PostProcessors = List[Dict[str, str]]


class ConfigError(ValueError):
    "a custom configuration error type"


class ArgumentValidationError(ArgumentTypeError, TypeError):
    "subclasses both argparse.ArgumentTypeError and TypeError"


class OpenablePathMeta(type):
    "Only here to make OpenablePath a callable class"

    def __call__(cls, filename: Union[Path, str]) -> Path:
        "checks that the filename is a valid path, and returns it"
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


class OpenablePath(metaclass=OpenablePathMeta):
    "Will only take a file that's able to be read"

    @classmethod
    def __get_validators__(
        cls,
    ) -> Iterable[Callable[[Union[Path, str]], Path]]:
        "enables pydantic to use this as a custom type"
        yield cls


class DirectoryMeta(type):
    "Only here to make Directory a callable class"

    def __call__(cls, filename: Union[Path, str, type(None)] = None) -> Path:
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

        log.debug("directory exists: '%(path)s'", {"path": path})

        temporary_file = path / f"{__name__}.temporary_file"
        assert not temporary_file.exists(), f"'{temporary_file}' must not already exist"
        try:
            temporary_file.touch()
        except OSError as err:
            message = "Cannot create '{temporary_file}' in '{path}'"
            log.exception(message)
            raise ArgumentValidationError(message) from err

        log.debug("removing temporary file '%(path)s'", {"path": temporary_file})
        temporary_file.unlink()

        return path


class Directory(metaclass=DirectoryMeta):
    "A type that indicates a directory that exists and is writeable"

    @classmethod
    def __get_validators__(
        cls,
    ) -> Iterable[Callable[[Union[Path, str, type(None)]], Path]]:
        "enables pydantic to use this as a custom type"
        yield cls
