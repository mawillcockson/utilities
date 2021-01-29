from pathlib import Path

VIDEOS_FOLDER = Path("C:/Users/Netflix/Videos/videos_from_youtube").resolve(strict=True)
PLAYLIST_FILE = Path("C:/Users/Netflix/Videos/videos.m3u8").resolve(strict=True)

videos = set()

for file in VIDEOS_FOLDER.glob("*"):
    if not file.is_file():
        continue
    
    videos.add(str(file.resolve(strict=True)))

PLAYLIST_FILE.write_text("\n".join(videos))