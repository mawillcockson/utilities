#python -m pip install --user --upgrade pip setuptools wheel
#python -m pip install --user --upgrade pipx
#python -m pipx ensurepath
#python -m pipx reinstall-all

youtube-dl `
    --batch-file C:\Users\Netflix\Videos\youtube_videos.txt `
	--download-archive C:\Users\Netflix\Videos\script_files_DO_NOT_DELETE\list_of_downloaded_video_ids.txt `
	--cookies C:\Users\Netflix\Videos\script_files_DO_NOT_DELETE\cache_file.txt `
	--cache-dir C:\Users\Netflix\Videos\script_files_DO_NOT_DELETE\youtube-dl_cache `
	--yes-playlist `
    --restrict-filenames `
    --no-overwrites `
    --no-call-home `
	--merge-output-format mkv `
    --geo-bypass-country us `
    --ignore-errors `
    --output 'C:\Users\Netflix\Videos\videos_from_youtube\%(id)s.%(ext)s'

python C:\Users\Netflix\Videos\script_files_DO_NOT_DELETE\generate_playlist.py