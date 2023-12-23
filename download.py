import re
import asyncio
import requests
from pytube import YouTube
from yt_dlp import YoutubeDL
from moviepy.editor import VideoFileClip

progress_message = None
last_message_text = None

async def download(update, context):
    url = context.user_data['url']
    format = context.user_data['format']

    thumbnail_picture = download_thumbnail(url)
    author = get_author(url)

    def my_hook(d):
        global progress_message
        global last_message_text
        progress_text = "Завантаження..."
        

        if d['status'] == 'downloading':
            percent_str = re.sub(r'\x1b\[[0-9;]*m', '', d['_percent_str'])
            if percent_str == '100.0%':
                progress_text = "Надсилання..."
            else:
                progress_text = f"Завантажено: {percent_str}"

        if not progress_message or last_message_text != progress_text:
            if progress_message:
                progress_message = progress_text
            else:
                progress_message = asyncio.get_event_loop().create_task(update.callback_query.edit_message_text(text=progress_text))
            last_message_text = progress_text


        # if d['status'] == 'downloading':
        #     asyncio.get_event_loop().create_task(context.bot.send_message(chat_id=context.user_data.get('chat_id'),
        #                             text="downloading..."))
        # elif d['status'] == 'd':
        #     pass
        # else:
        #     asyncio.get_event_loop().create_task(context.bot.send_message(chat_id=context.user_data.get('chat_id'),
        #                             text="Зараз буде"))
        
    await update.callback_query.edit_message_text(text="Знайшов, завантажую...")
    with YoutubeDL() as ydl:
        info_dict = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info_dict)
        print(format)
        if format == 'mp3':
            with VideoFileClip(filename) as video_clip:
                audio_clip = video_clip.audio
                audio_filename = filename.rsplit(".", 1)[0] + ".mp3"
                audio_clip.write_audiofile(audio_filename)
            return audio_filename, author, thumbnail_picture

        return filename, author, thumbnail_picture 
    
    
def download_thumbnail(url):
    yt = YouTube(url)
    thumbnail_url = yt.thumbnail_url
    video_title = yt.title
    # Remove invalid characters from filename
    filename = re.sub(r'[\\/*?:"<>|]', "", video_title)
    response = requests.get(thumbnail_url)
    with open(f'{filename}.jpg', 'wb') as file:
        file.write(response.content)
        
    return f'{filename}.jpg'


def get_author(url):
    yt = YouTube(url)
    return yt.author


