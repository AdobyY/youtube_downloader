import re
from yt_dlp import YoutubeDL
from moviepy.editor import VideoFileClip
from pytube import YouTube

import requests

progress_message = None
last_message_text = None

def download(url, format, context):
    global progress_message
    global last_message_text

    # Use the function
    download_thumbnail(url)

    def my_hook(d, context):
        global progress_message
        global last_message_text

        if d['status'] == 'downloading':
            percent_str = re.sub(r'\x1b\[[0-9;]*m', '', d['_percent_str'])
            if percent_str == '100.0%':
                progress_text = "Надсилання..."
            else:
                progress_text = f"Завантажено: {percent_str}"

            chat_id = context.user_data.get('chat_id')

            if chat_id:
                if not progress_message or last_message_text != progress_text:
                    if progress_message:
                        progress_message.edit_text(progress_text)
                    else:
                        progress_message = context.bot.send_message(chat_id=chat_id, text=progress_text)
                    
                    last_message_text = progress_text
            else:
                print("chat_id not found in user_data")

    with YoutubeDL({'format': 'best', 'progress_hooks': [lambda d: my_hook(d, context)]}) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info_dict)
        author = get_author(url)
        if format == 'mp3':
            

            with VideoFileClip(filename) as video_clip:
                audio_clip = video_clip.audio
                audio_filename = filename.rsplit(".", 1)[0] + ".mp3"
                audio_clip.write_audiofile(audio_filename)
            return audio_filename, author

        return filename, author
    
def download_thumbnail(url):
    yt = YouTube(url)
    thumbnail_url = yt.thumbnail_url
    video_title = yt.title
    # Remove invalid characters from filename
    filename = re.sub(r'[\\/*?:"<>|]', "", video_title)
    response = requests.get(thumbnail_url)
    with open(f'{filename}.jpg', 'wb') as file:
        file.write(response.content)


def get_author(url):
    yt = YouTube(url)
    return yt.author


