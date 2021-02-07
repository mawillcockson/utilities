# mypy: allow-any-expr
"""
This is the main file that is run when the tool is used
"""
import logging
from pathlib import Path
from typing import List, Optional, Sequence

import decli
from pydantic import BaseModel  # pylint: disable=no-name-in-module
from youtube_dl import YoutubeDL

from . import __version__
from .config import load_config
from .logging import log
from .types import Directory, OpenablePath, PostProcessors
from .utils import filter_inaccessible, pretty

DEFAULT_OUTPUT_TEMPLATE = "%(id)s.%(ext)s"
DEFAULT_FORMAT = "bestvideo+bestaudio/best"
DEFAULT_DOWNLOAD_ARCHIVE_NAME = "list_of_downloaded_videos.txt"
DEFAULT_COOKIEFILE_NAME = "youtube_dl_browser_cookies.txt"


INTERFACE_SPEC = {
    "description": "Manages playlists of videos",
    "add_help": True,
    "allow_abbrev": True,
    "arguments": [
        {
            "name": "--version",
            "action": "version",
            "version": f"%(prog)s {__version__}",
            "help": "prints the version",
        },
        {
            "name": ["-c", "--config"],
            "dest": "config_file",
            "type": OpenablePath,
            "help": "path to config file",
        },
        {
            "name": ["--debug"],
            "dest": "debug",
            "action": "store_true",
            "help": "print verbose messages",
        },
    ],
}


class YouTubeDLOptions(BaseModel):
    """
    options for youtube-dl

    see:
    https://github.com/ytdl-org/youtube-dl/blob/3e4cedf9e8cd3157df2457df7274d0c842421945/youtube_dl/YoutubeDL.py#L137-L312
    """

    verbose: bool = False
    outtmpl: str = DEFAULT_OUTPUT_TEMPLATE
    ignoreerrors: bool = False
    nooverwrites: bool = True
    logger_name: str = "youtube-dl"
    noplaylist: bool = False
    fixup: str = "detect_or_warn"
    call_home: bool = False
    no_color: bool = True
    format: str = DEFAULT_FORMAT
    cachedir: Directory
    download_archive: Path
    cookiefile: Path
    postprocessors: Optional[PostProcessors] = None


class UrlsFile(BaseModel):
    "a file that has urls in it"
    filepath: OpenablePath
    urls: List[str]


class VideoFile(BaseModel):
    """
    a video file with youtube-dl metadata
    """

    filepath: OpenablePath


class Playlist(BaseModel):
    "a file and its corresponding video files"
    filepath: OpenablePath
    videos: List[OpenablePath]


def urls_in_file(url_file: Path) -> UrlsFile:
    "collects the urls from a file"
    if not url_file.is_file():
        raise ValueError(f"'{url_file}' is not a file")

    urls: List[str] = list()
    with url_file.open(mode="rt") as file:
        for line in file:
            url = line.strip()
            urls.append(url)
            log.debug("added url from '%s' -> '%s'", url_file, url)

    log.debug(urls)
    # NOTE:BUG should catch pydantic errors
    return UrlsFile(filepath=url_file, urls=urls)


def gather_urls(urls_folder: Path) -> List[UrlsFile]:
    "finds all of the files in the urls folder and collects the urls from each"
    if not urls_folder.is_dir():
        raise ValueError(f"'{urls_folder}' is not a directory")

    log.debug("searching for playlists in '%s'", urls_folder)

    files_and_urls: List[UrlsFile] = []
    for file in urls_folder.glob("*"):
        files_and_urls.append(urls_in_file(file))

    if not files_and_urls:
        log.error("no playlists found")

    # NOTE:BUG should catch pydantic errors
    return files_and_urls


def download_videos(
    urls_file: UrlsFile, ytdl_options: YouTubeDLOptions, force: bool = False
) -> List[VideoFile]:
    "tries to use youtube-dl to download all the urls"
    # Prepare youtube-dl options
    ytdl_options_dict = ytdl_options.dict(exclude_none=True)
    ytdl_options_dict["logger"] = logging.getLogger(ytdl_options_dict["logger_name"])
    ytdl_options_dict.pop("logger_name")
    ytdl_options_dict["logger"].setLevel(logging.DEBUG)
    if force:
        ytdl_options_dict.pop("download_archive")

    log.debug("youtube-dl options:\n%s", pretty(ytdl_options_dict))

    ytdl = YoutubeDL(ytdl_options_dict)
    video_files: List[VideoFile] = []
    for url in urls_file.urls:
        video_info = ytdl.extract_info(url=url, download=True)
        video_info["filepath"] = ytdl.prepare_filename(video_info)
        video_files.append(VideoFile.parse_obj(video_info))

    return video_files


def make_playlist(
    urls_file: UrlsFile,
    playlists_folder: Path,
    video_files: List[Path],
) -> Playlist:
    "takes video files and a playlist name, and makes the playlist"
    # Build playlist file name, and create it if it doesn't exist
    playlist_name = OpenablePath(urls_file.filepath).stem
    playlist_file = OpenablePath(
        (Directory(playlists_folder) / playlist_name).with_suffix(".m3u8")
    )

    # Read and update playlist
    current_contents = playlist_file.read_text().splitlines()
    current_videos = list(filter_inaccessible(current_contents))
    updated_contents = [str(path) for path in current_videos]
    if current_contents != updated_contents:
        log.debug(
            (
                "fixed playlist '%(playlist_file)s'\n"
                "old contents:\n"
                "%(old_contents)s\n"
                "new contents:\n"
                "%(new_contents)s\n"
            ),
            {
                "playlist_file": playlist_file,
                "old_contents": "\n".join(current_contents),
                "new_contents": "\n".join(updated_contents),
            },
        )
        playlist_file.write_text("\n".join(updated_contents))

    # Filter out the new videos
    new_videos = set(video_files) - set(current_videos)
    if not new_videos:
        log.debug("no change to playlist '%s'", playlist_file)
        return Playlist(filepath=playlist_file, videos=current_videos)

    # Add new video files in the order that they appear in video_files
    for video_file in video_files:
        if not video_file in new_videos:
            continue

        log.debug(
            "add to playlist '%(playlist_file)s' <- '%(video_file)s'",
            {"playlist_file": playlist_file, "video_file": video_file},
        )
        current_videos.append(video_file)
        # Prevents duplicates from being added, in conjunction with the "in"
        # check at the beginning of the loop.
        # set.discard() does not raise KeyError if key does not exist
        new_videos.discard(video_file)

    log.info("playlist updated '%s'", playlist_file)
    return Playlist(filepath=playlist_file, videos=current_videos)


def main(argv: Optional[Sequence[str]] = None) -> None:
    """
    Parses the cli arguments and runs the appropriate commands
    """
    parser = decli.cli(INTERFACE_SPEC)
    if argv is not None:
        args = parser.parse_args(argv)
    else:
        args = parser.parse_args()

    if args.debug:
        log.setLevel("DEBUG")
        log.debug("args: %(args)s", {"args": args})

    settings = load_config(args.config_file)

    download_archive = settings.cache / DEFAULT_DOWNLOAD_ARCHIVE_NAME
    cookiefile = settings.cache / DEFAULT_COOKIEFILE_NAME

    # The output template that youtube-dl will use to generate filenames for
    # downloaded media
    outtmpl = str(settings.videos / DEFAULT_OUTPUT_TEMPLATE)

    ytdl_options = YouTubeDLOptions(
        verbose=args.debug,
        cachedir=settings.cache,
        download_archive=download_archive,
        cookiefile=cookiefile,
        outtmpl=outtmpl,
    )

    urls_files = gather_urls(urls_folder=settings.urls)
    for file in urls_files:
        video_files = download_videos(urls_file=file, ytdl_options=ytdl_options)
        make_playlist(
            urls_file=file,
            playlists_folder=settings.playlists,
            video_files=[video.filepath for video in video_files],
        )


if __name__ == "__main__":
    main()
