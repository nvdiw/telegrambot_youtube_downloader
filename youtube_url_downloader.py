import os
from typing import Optional
import yt_dlp

DOWNLOAD_DIR = "./downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_youtube(
    url: str,
    output_dir: str = DOWNLOAD_DIR,
    filename_template: str = "%(title)s.%(ext)s",
    audio_only: bool = False,
    max_filesize_bytes: Optional[int] = None
) -> dict:
    ydl_opts = {
        "outtmpl": os.path.join(output_dir, filename_template),
        "noplaylist": True,
        "quiet": False,
        "no_warnings": True,
        "progress_hooks": [lambda d: print_progress_hook(d)],
    }

    if max_filesize_bytes is not None:
        ydl_opts["max_filesize"] = max_filesize_bytes

    if audio_only:
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        ydl_opts.update({
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return {"success": True, "info": info}
    except Exception as e:
        return {"success": False, "error": str(e)}

def print_progress_hook(d):
    status = d.get("status")
    if status == "downloading":
        eta = d.get("eta")
        speed = d.get("speed")
        downloaded = d.get("downloaded_bytes")
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        print(f"downloading... {downloaded}/{total} bytes, speed={speed}, eta={eta}s", end="\r")
    elif status == "finished":
        print("\ndownload finished, now post-processing...")

if __name__ == "__main__":
    url = input("Enter the YouTube video URL: ").strip()
    audio_only_input = "n"  #input("Download audio only? (y/n): ").strip().lower()
    audio_only = audio_only_input == "y"

    result = download_youtube(url, audio_only=audio_only)
    if result.get("success"):
        info = result["info"]
        title = info.get("title")
        filepath = info.get("_filename") or info.get("requested_downloads", [{}])[0].get("filepath")
        print(f"\nOK — downloaded: {title}\nSaved to: {filepath}")
    else:
        print("Error:", result.get("error"))
