import argparse
import json
import urllib.request
from urllib.parse import parse_qs, urlparse
from pathlib import Path
import yt_dlp

"""Formatting Helpers"""
def format_timestamp(milliseconds):
    seconds = int(milliseconds) // 1000
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    return f"{minutes:02}:{seconds:02}"


def format_caption_blocks(events, block_seconds=20):
    blocks = []
    block_start = None
    words = []

    for event in events:
        text = " ".join(
            seg.get('utf8', '').strip()
            for seg in event.get('segs', [])
            if seg.get('utf8', '').strip()
        )
        if not text:
            continue

        start = event.get('tStartMs', 0)
        if words and start - block_start >= block_seconds * 1000:
            blocks.append(f"[{format_timestamp(block_start)}] {' '.join(words)}")
            words = []

        if not words:
            block_start = start
        words.append(text)

    if words:
        blocks.append(f"[{format_timestamp(block_start)}] {' '.join(words)}")

    return "\n\n".join(blocks)


def format_upload_date(upload_date):
    if upload_date and len(upload_date) == 8 and upload_date.isdigit():
        return f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    return "Unknown"


"""Main get methods"""
def get_youtube_captions(video_url, lang='en'):
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
        except yt_dlp.utils.DownloadError as e:
            raise RuntimeError(
                "yt-dlp failed to fetch video information. YouTube may have changed "
                "how videos are served. Keep yt-dlp up to date with "
                "`venv/bin/python -m pip install --upgrade yt-dlp` and try again. "
                f"Details: {e}"
            ) from e

        # Extract our subtitles config for our language of choice
        subtitles = info.get('subtitles', {})
        if lang not in subtitles:
            subtitles = info.get('automatic_captions', {})

        if lang not in subtitles:
            raise RuntimeError(f"No captions found for language code: {lang}")
            
        # Target the json3 format explicitly for easy parsing
        # Other formats include srv1, srv2, srv3, ttml,srt, vtt
        sub_formats = subtitles[lang]
        json_url = None
        for fmt in sub_formats:
            if fmt.get('ext') == 'json3':
                json_url = fmt.get('url')
                break

        if not json_url:
            raise RuntimeError("Could not find text-parsable json3 format for this video.")
            
        # Fetch the JSON structure from YouTube's servers
        try:
            with urllib.request.urlopen(json_url) as response:
                payload = json.loads(response.read().decode('utf-8'))
        except Exception as e:
            raise RuntimeError(f"Failed to download or parse caption track: {e}") from e
            
        metadata = (
            f"Title: {info.get('title') or 'Unknown'}\n"
            f"Channel: {info.get('channel') or info.get('uploader') or 'Unknown'}\n"
            f"Upload date: {format_upload_date(info.get('upload_date'))}"
        )
        captions = format_caption_blocks(payload.get('events', []))
        return f"{metadata}\n\n{captions}"

def get_video_id(video_url):
    parsed = urlparse(video_url)
    host = (parsed.hostname or "").lower()

    if host in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif parsed.path.startswith(("/shorts/", "/live/", "/embed/")):
            video_id = parsed.path.split("/")[2]
        else:
            video_id = ""
    elif host in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/").split("/")[0]
    else:
        video_id = ""

    if not video_id or not all(char.isalnum() or char in "_-" for char in video_id):
        raise ValueError("Please provide a valid YouTube video URL.")
    return video_id


# When run as a standalone script, save the transcript as a file.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Save a YouTube video's captions.")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--lang", default="en", help="Caption language code (default: en)")
    args = parser.parse_args()

    try:
        video_id = get_video_id(args.url)
        captions = get_youtube_captions(args.url, lang=args.lang)
    except (ValueError, RuntimeError) as exc:
        parser.exit(1, f"Error: {exc}\n")

    transcripts_dir = Path(__file__).resolve().parent / "transcripts"
    transcripts_dir.mkdir(exist_ok=True)
    transcript_path = transcripts_dir / f"{video_id}.txt"
    transcript_path.write_text(captions, encoding="utf-8")

    print(f"Captions stored in {transcript_path}")
