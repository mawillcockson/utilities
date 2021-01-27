"""
This tool relies on dumb-pypi to build a static package index for libguestfs
Python bindings

dumb-pypi:
https://github.com/chriskuehl/dumb-pypi

libguestfs Python bindings:
https://download.libguestfs.org/python/

It requires Python 3.6+
"""
import argparse
import logging
import math
import re
import sys
from argparse import ArgumentTypeError, Namespace
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence, Union
from urllib.parse import ParseResult, urlparse, urlunparse
from urllib.request import urlopen

from bs4 import BeautifulSoup
from dumb_pypi.main import main as dumb_pypi_main
from pydantic import BaseModel  # pylint: disable=no-name-in-module

from .utils import orjson_dumps, orjson_loads

assert sys.version_info >= (3, 9,), (
    "Python 3.9+ required\n" f"Detected Python version: {sys.version}"
)


GUESTFS_PACKAGE_INDEX_URL = "https://download.libguestfs.org/python/"
GUESTFS_UPLOAD_TIME_FORMAT = "%Y-%m-%d %H:%M"
PACKAGE_LIST_JSON_FILE = "package_list.json"


guestfs_distribution_file_re = re.compile(
    r"^guestfs-(?P<version>(\d+\.){2}\d+)\.tar\.gz$"
)
guestfs_upload_time_re = re.compile(
    r"^\s*(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2}) (?P<hour>\d{2}):(?P<minute>\d{2})\s*$"
)
log = logging.getLogger(__name__)


def setup_logging(level: int = logging.WARN) -> None:
    "configure builtin logging"
    logging.basicConfig(level=level)


class ArgumentValidationError(ArgumentTypeError, TypeError):
    "subclasses both argparse.ArgumentTypeError and TypeError"


class DistributionMetadata(BaseModel):
    "metadata for each distribution file"
    filename: str
    hash: Optional[str]
    upload_timestamp: Optional[int]

    class Config:
        "pydantic configuration class for DistributionMetadata"
        # NOTE: Supposed to help speed up JSON encoding and decoding
        # from:
        # https://pydantic-docs.helpmanual.io/usage/exporting_models/#custom-json-deserialisation
        json_loads = orjson_loads
        json_dumps = orjson_dumps
        allow_mutation = False


class DirectoryPathMeta(type):
    "Only here to make DirectoryPath a callable class"

    def __call__(cls, filename: Union[Path, str]) -> Path:
        "checks that the filename is a valid directory, and returns it"
        path = Path(filename).resolve()
        if not path.is_dir() and path.exists():
            raise ArgumentValidationError(f"'{path}' exists and is not a directory")

        try:
            path.mkdir(exist_ok=True)
        except OSError as err:
            message = f"directory '{path}' does not exist and it cannot be created"
            log.error(message, exc_info=True)
            raise ArgumentValidationError(message) from err

        deleteable_file = path / "deleteable_file"
        assert (
            not deleteable_file.exists()
        ), f"'{deleteable_file}' exists, and should not"

        try:
            deleteable_file.touch()
        except OSError as err:
            message = f"Can't create files in '{path}'"
            log.error(message, exc_info=True)
            raise ArgumentValidationError(message) from err

        deleteable_file.unlink(missing_ok=True)

        return path


class DirectoryPath(metaclass=DirectoryPathMeta):
    """
    Takes a str or Path that points to path that is either a directory, or
    where a directory can be made
    """


def fetch_current_index(index_url: str = GUESTFS_PACKAGE_INDEX_URL) -> BeautifulSoup:
    "retrieves the current guestfs package index from the web as a BeautifulSoup"
    with urlopen(index_url) as index_result:
        if not index_result.msg == "OK":
            raise ValueError(
                f"'{index_url}' did not return a valid response:\n{index_result}"
            )

        return BeautifulSoup(index_result, "lxml")


def parse_upload_time(upload_time_text: str) -> int:
    "parses the guestfs upload time into a POSIX timestamp"
    upload_time = datetime.strptime(
        upload_time_text.strip(), GUESTFS_UPLOAD_TIME_FORMAT
    )
    as_posix_timestamp = upload_time.timestamp()
    return int(math.floor(as_posix_timestamp))


def find_links(
    index_url: str = GUESTFS_PACKAGE_INDEX_URL,
) -> list[DistributionMetadata]:
    "gathers links to guestfs packages from the index"
    parsed_index = urlparse(index_url)
    current_index = fetch_current_index(index_url=index_url)
    distribution_file_anchors = current_index.find_all(
        "a", href=guestfs_distribution_file_re
    )

    distribution_file_metadata: list[DistributionMetadata] = []
    for anchor_tag in distribution_file_anchors:
        url_parts = ParseResult(
            scheme=parsed_index.scheme,
            netloc=parsed_index.netloc,
            path=parsed_index.path + anchor_tag.attrs["href"],
            params=parsed_index.params,
            query=parsed_index.query,
            fragment=parsed_index.fragment,
        )
        url = urlunparse(url_parts)

        try:
            upload_time_text = anchor_tag.parent.next_sibling.text
        except AttributeError:
            # pylint: disable=raise-missing-from
            raise ValueError(
                "Cannot parse index page:\n"
                f"{current_index}\n\n"
                f"can't find timestamp tag for -> {anchor_tag}"
            )

        if not guestfs_upload_time_re.match(upload_time_text):
            raise ValueError(
                f"Cannot interpret upload time: {upload_time_text}\n"
                f"for {anchor_tag}"
            )

        upload_timestamp = parse_upload_time(upload_time_text)

        distribution_file_metadata.append(
            DistributionMetadata(
                url=url,
                filename=anchor_tag.attrs["href"],
                hash=None,
                upload_timestamp=upload_timestamp,
            )
        )

    return distribution_file_metadata


def compute_hashes(
    links: list[DistributionMetadata],
    temporary_directory: Union[Path, str],
    old_package_list_json: Union[Path, str, None] = None,
) -> list[DistributionMetadata]:
    """
    downloads all the distribution package files according to the distribution
    metadata, and computes their hashes, then discards the distribution files

    if passed a file with metadata from previous runs, then it will only
    compute the missing hashes
    """
    raise NotImplementedError("sorry :(")


def write_package_list_json(
    metadata: list[DistributionMetadata], path: Union[Path, str]
) -> Path:
    "writes the distribution metadata out to a file"
    package_list_json_file = Path(path)
    if not package_list_json_file.is_file() and package_list_json_file.exists():
        raise FileNotFoundError(f"'{path}' already exists and is not a file")

    # NOTE: Writing out the file this way, as opposed to with
    # Path.write_text(), ensures that, if there's a JSON serialization error,
    # the entries that can be serialized that are before the problematic entry
    # will be written out.
    # This might save some computation time if hashes are being calculated, as
    # on the next run, the hashes that were calculated and written out won't
    # have to be recalculated.
    with package_list_json_file.open(mode="wt") as metadata_file:
        for distribution_file_metadata in metadata:
            metadata_file.write(
                distribution_file_metadata.json(exclude_none=True) + "\n"
            )

    return package_list_json_file


def run_dumb_pypi(
    metadata: list[DistributionMetadata],
    distribution_path: Union[Path, str],
    packages_url: str = GUESTFS_PACKAGE_INDEX_URL,
) -> None:
    "runs dumb-pypi to generate the package index files"
    output_directory = Path(distribution_path).resolve(strict=True)
    if not output_directory.is_dir():
        raise NotADirectoryError(f"expected '{output_directory}' to be a directory")

    package_list_json_path = write_package_list_json(
        metadata=metadata, path=distribution_path / PACKAGE_LIST_JSON_FILE
    )
    dumb_pypi_main(
        argv=[
            "--no-generate-timestamp",
            "--package-list-json",
            str(package_list_json_path),
            "--output-dir",
            str(distribution_path),
            "--packages-url",
            packages_url,
        ]
    )


def parse_args(argv: Optional[Sequence[str]] = None) -> Namespace:
    "parses the command line arguments"
    parser = argparse.ArgumentParser(
        description="A wrapper for dumb-pypi to generate an index for libguestfs Python bindings"
    )

    parser.add_argument(
        "directory",
        type=DirectoryPath,
        help="the directory into which the generated index files will be put",
    )
    parser.add_argument(
        "--hash",
        action="store_true",
        help="download all packages and add hashes to index",
    )
    parser.add_argument(
        "--debug", action="store_true", help="print out debugging statements to stderr"
    )

    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    "the main function executed when this tool is run"
    args = parse_args(argv=argv)

    if args.debug:
        setup_logging(level=logging.DEBUG)
    else:
        setup_logging()

    links = find_links()

    if args.hash:
        all_metadata = compute_hashes(links=links, temporary_directory=args.temp_dir)
    else:
        all_metadata = links
    run_dumb_pypi(metadata=all_metadata, distribution_path=args.directory)


if __name__ == "__main__":
    main()
