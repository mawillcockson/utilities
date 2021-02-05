# Playlist Generator

This tool helps download videos, and organize them into playlists.

## Installation

[`pipx`][] is the preferred way to install this tool. First, [install `pipx`][], then:

```sh
pipx install "git+https://github.com/mawillcockson/utilities#egg=mw_playlist_generator&subdirectory=mw_playlist_generator"
```

This should make the `playlist-generator` command line tool available.

## Use

This tool takes input mainly in the form of text files specifying which videos to download. Its only command-line argument is for specifying a configuration file:

```sh
playlist-generator --config configuration.ini
```

The configuration file looks like this:

```ini
[playlists]
urls = urls/
playlists = playlists/
videos = Videos/
scripts = scripts_DO_NOT_DELETE/
```

### Configuration file

The configuration file can be placed anywhere. Any paths in the file that are not absolute, are **relative to the location of the configuration file**.

The `[playlists]` section header is required.

#### `urls`

The folder of URL lists.

Each file in the folder should be a text file. The name of the playlist file will be used as the name of the resulting playlist.

#### `playlists`

The folder where the generated playlist files are stored.

#### `videos`

The folder where the tool should store videos.

All videos stored in this folder will be named by video ID. The video IDs are largely globally unique, so there should't be much of a problem with storing them all in one place.

#### `scripts`

The folder that's used by this tool to store files it needs to function. The contents of this folder should probably not be modified manually.

## Disclaimer

Though anyone is free to use this, I only intend to support my own workflow.

This uses [`youtube-dl`][] internally, but only exposes a tiny fraction of its features. For a much more mature and general-purpose tool, check out [`youtube-dl`][].


[`youtube-dl`]: <https://github.com/ytdl-org/youtube-dl> "youtube-dl on GitHub"
