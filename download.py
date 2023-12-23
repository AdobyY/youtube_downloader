import re
from yt_dlp import YoutubeDL
from moviepy.editor import VideoFileClip
from pytube import YouTube

import requests
import asyncio

async def download(update, context):
    url = context.user_data['url']
    format = context.user_data['format']
    # Use the function
    thumbnail_picture = download_thumbnail(url)
    author = get_author(url)


    def my_hook(d):
        asyncio.get_event_loop().create_task(context.bot.send_message(chat_id=context.user_data.get('chat_id'),
                                 text="dsafdfa"))
       

    with YoutubeDL({'format': 'best', 
                    'progress_hooks': [my_hook]}) as ydl:
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


