# Playlist Generator

This is the first iteration of these sets of scripts. These have many, many shortcomings:

- Hard-coded paths
- Only generates one playlist
- Does not handle errors consistently
- Requires managing text files and manually running a script
- Videos are hard to remove
- Supports exactly one workflow

I think this could be done better.

My first goal is to consolidate the functionality into one tool. This would really just be an implementation detail, but there are some goals, like making it easier to associate videos with urls, to make removing ideos easier, I can take advantage of [the very nice API `youtube-dl` provides embedding](https://github.com/ytdl-org/youtube-dl#embedding-youtube-dl).

The goals of this current rewrite are:

- Make it easier to generate and update multiple playlists

That's it for now.

I think with a more complete framework in place, even a simple one, it will be easier to plan the other features.

The stretch goals for this as a whole would be:

- Make it easy to remove a specific video, and ensure the corresponding source is remembered as undesirable
- Remove the need for manually running the tool: it is run automatically on file changes
- Provide installation through a single command or executable, with no dependencies on existing tools
- Automatic updates
- Provide a web interface for managing and playing playlists of videos
