from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
from typing import Optional
import warnings
import os
import yt_dlp

warnings.filterwarnings("ignore", category=UserWarning)

# Bot token from BotFather
TOKEN = "YOUR_TOKEN"

DOWNLOAD_DIR = "./downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Variable to store the last message with buttons
last_message_id = None
# Dictionary to store user choices {user_id: True}
users_done = {}


##############################################################
# TELEGRAM BOT
##############################################################

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_message_id, users_done

    user_id = update.message.from_user.id
    # Reset user's choice so they can select again
    if user_id in users_done:
        del users_done[user_id]

    keyboard = [
        [InlineKeyboardButton("Option 1 ✅", callback_data="1")],
        [InlineKeyboardButton("Option 2 ✅", callback_data="2")],
        [InlineKeyboardButton("Option 3 ✅", callback_data="3")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send a new message and store message_id
    msg = await update.message.reply_text("Choose an option:", reply_markup=reply_markup)
    last_message_id = msg.message_id

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_message_id, users_done
    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    # Check if it's the last message
    if query.message.message_id != last_message_id:
        await query.answer(text="This button is inactive.", show_alert=True)
        return

    # Check if the user has already made a choice
    if users_done.get(user_id):
        await query.answer(text="You have already made a choice.", show_alert=True)
        return

    # Register user's choice
    users_done[user_id] = True

    if query.data == "download_video_yes":
        # await query.message.reply_text(f"You selected option {query.data}")
        await query.message.reply_text("Downloading video...")
        result = download_youtube(youtube_url)

        if result.get("success"):
            downloaded_file = result.get("downloaded_file")  # downloaded file address
            await query.message.reply_text("Download complete, sending video now...")

            # sending video to user
            with open(downloaded_file, "rb") as video_file:
                await query.message.reply_video(video=video_file)

        else:
            await query.message.reply_text(f"Error downloading: {result.get('error')}")
            
    else:
        await query.message.reply_text("Okay For more options write: /start")

async def youtube_dl_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply to /youtube command."""
    await update.message.reply_text("Send a YouTube URL now.")

async def check_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if is_youtube_url(text):
        global youtube_url
        youtube_url = text
        info_youtube_url = get_youtube_video_info(youtube_url)

        if "size_mb" in info_youtube_url:
            
            global last_message_id, users_done

            user_id = update.message.from_user.id
            # Reset user's choice so they can select again
            if user_id in users_done:
                del users_done[user_id]

            keyboard = [
                [InlineKeyboardButton(f"Video size: {info_youtube_url["size_mb"]} Mb", callback_data="download_video_yes")],
                [InlineKeyboardButton("Download", callback_data="download_video_yes")],
                [InlineKeyboardButton("Cancel", callback_data="download_video_cancel")],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            msg = await update.message.reply_text("Video name is: \n" + info_youtube_url["title"], reply_markup=reply_markup)            
            last_message_id = msg.message_id

            await update.message.reply_text("Wanna download ?")

    else:
        await update.message.reply_text("This is not a valid YouTube URL. Please send a valid one.")


##############################################################
# YOUTUBE PROGSSES
##############################################################

def is_youtube_url(text: str) -> bool:
    text = text.lower()
    return "youtube.com" in text or "youtu.be" in text


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
            downloaded_file = info.get("_filename") or info.get("requested_downloads", [{}])[0].get("filepath")
            return {"success": True, "info": info, "downloaded_file": downloaded_file}
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
        print("\nDownload finished, now post-processing...")

def get_youtube_video_info(url: str):
    
    ydl_opts = {"quiet": True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)  # just get information
            filesize = info.get('filesize') or info.get('filesize_approx')
            title = info.get('title')

            if filesize:
                size_mb = round(filesize / (1024 * 1024), 2)
                return {"title": title, "size_mb": size_mb}
            else:
                return {"title": title, "size_mb": None, "error": "Couldn't get file size."}
    except Exception as e:
        return {"error": str(e)}
    

##############################################################
# MAIN APP
##############################################################

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # /start command
    app.add_handler(CommandHandler("start", start))
    
    # /youtube command
    app.add_handler(CommandHandler("youtube", youtube_dl_cmd))


    # handle text messages (YouTube URLs)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_youtube))


    # handle buttons
    app.add_handler(CallbackQueryHandler(button))



    # start bot (long polling)
    app.run_polling()


if __name__ == "__main__":
    main()
