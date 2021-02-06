"""
everything to do with the configuration file

the --config parameter
"""
from configparser import ConfigParser, ParsingError
from io import StringIO
from pathlib import Path
from typing import Union

from pydantic import BaseSettings, Extra  # pylint: disable=no-name-in-module

from .logging import log
from .types import ConfigError, Directory, OpenablePath
from .utils import pretty


class Settings(BaseSettings):
    """
    A class that makes dealing with settings easier
    """

    urls: Directory
    playlists: Directory
    videos: Directory
    cache: Directory
    config: OpenablePath

    class Config:
        """
        a pydantic configuration class
        """

        env_prefix = "MW_PLAYLISTS_"
        allow_mutation = False
        extras = Extra.forbid


def save_config(config: ConfigParser, settings: Settings) -> str:
    """
    save the configuration to the file indicated in settings
    returns the config file contents as a string
    """
    # NOTE: Because neither Directory nor OpenablePath are subclasses of Path,
    # this wrapping is needed in order to compare them
    if Path(str(settings.cache)) == Path(settings.config.parent):
        settings_dict = settings.dict(exclude={"config", "cache"})
    else:
        settings_dict = settings.dict(exclude={"config"})

    config_dict = {"playlists": settings_dict}
    config.read_dict(config_dict, source=f"{__name__}.save_config.config_dict")

    # Write the configuration into an in-memory string
    config_string = StringIO()
    config.write(config_string, space_around_delimiters=True)
    # Since the .read() method reads from the current position in the file, and
    # writing to a file leaves the position at the end of the file, a .seek()
    # is needed to move the position to the beginning of the file, so that it
    # can be read from the start
    config_string.seek(0)
    config_text = config_string.read()
    log.debug("saved configuration:\n%s", config_text)

    return config_text


def load_config(path: Union[str, Path]) -> Settings:
    "loads and validates the configuration"
    config_file = Path(path).resolve(strict=True)

    if not config_file.is_file():
        log.debug("config file '%s' not a file", config_file)
        raise ConfigError(f"'{config_file}' is not a file")

    # The default value for the cache directory is the same directory the
    # config file is in
    config = ConfigParser(defaults={"cache": "./"})

    config_text = config_file.read_text()
    try:
        config.read_string(config_text)
    except ParsingError as err:
        message = f"error parsing config:\n{config_text}"
        log.exception(message)
        raise ConfigError(message) from err

    if not config.has_section("playlists"):
        message = f"'{config_file} missing [playlists] section"
        log.debug(message)
        raise ConfigError(message)

    section = config["playlists"]

    for field in ["urls", "videos", "playlists"]:
        if not section.get(field, None):
            raise ConfigError(f"config file '{config_file}' missing field: '{field}'")

    config_dir = config_file.parent
    urls = Directory(config_dir / section["urls"])
    videos = Directory(config_dir / section["videos"])
    playlists = Directory(config_dir / section["playlists"])
    cache = Directory(config_dir / section["cache"])

    settings = Settings(
        urls=urls, videos=videos, playlists=playlists, cache=cache, config=config_file
    )
    log.debug("loaded config:\n%s", pretty(settings.dict()))

    return settings
