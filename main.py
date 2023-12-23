import logging
from urllib.parse import urlparse

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import filters, Application,CallbackContext, CallbackQueryHandler, MessageHandler, CommandHandler, ContextTypes
import os
import re
import json
import time
from download import download
from datetime import datetime
from telegram import InputFile
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('TEST_TOKEN')

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Надішліть своє посилання")


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    await query.answer()
    context.user_data['chat_id'] = update.effective_chat.id
    context.user_data['format'] = query.data
    context.user_data['timestamp'] = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    context.user_data['user_id'] = update.effective_user.id
    context.user_data['user_name'] = update.effective_user.first_name + " " + update.effective_user.last_name
    context.user_data['username'] = update.effective_user.username
    context.user_data['url'] = context.user_data.get('url')

    # Збереження даних про користувача та посилання в JSON-файл
    save_user_data(context.user_data)

    file_path, author, thumbnail = await download(context.user_data['url'], context.user_data['format'], context)
    if file_path:
        await send_file(file_path, author, thumbnail, update)            
    else:
        await update.message.reply_text('Невірне посилання. Будь ласка, надішліть коректне посилання.')



async def save_user_data(user_data):
    # Задайте шлях до файлу JSON
    json_file_path = 'user_data.json'

    if not os.path.exists(json_file_path):
        # Якщо файл не існує, створіть пустий словник
        data = {}
    else:
        # Якщо файл існує, зчитайте його дані
        with open(json_file_path, 'r') as file:
            data = json.load(file)

    # Збереження даних про користувача та посилання
    user_id = str(user_data['user_id'])
    if user_id not in data:
        data[user_id] = []

    data[user_id].append({
        'timestamp': user_data['timestamp'],
        'url': user_data['url'],
        'format': user_data['format'],
        'user_name': user_data['user_name'],
        'username': user_data['username']
    })

    # Збереження оновлених даних у файл JSON
    with open(json_file_path, 'w') as file:
        json.dump(data, file, indent=2)


async def send_file(file_path, author, thumbnail, update):
    clean_filename = re.sub(r'\s*\[.*?\]', '', file_path)
    #photo_name = clean_filename.rsplit(".", 1)[0] + ".jpg"
    video_filename = file_path.rsplit(".", 1)[0] + ".mp4"
    file_extension = clean_filename[-3:]
    
    if(file_extension=="mp3"):
        with open(file_path, 'rb') as file:
            with open(thumbnail, 'rb') as photo:
                await update.callback_query.message.reply_audio(audio=file_path, title=clean_filename,
                                          thumbnail=thumbnail, performer=author)
                photo.close()
            file.close()

        if os.path.exists(video_filename):
            os.remove(video_filename)
        if os.path.exists(thumbnail):
            os.remove(thumbnail)
        if os.path.exists(file_path):
            os.remove(file_path)

    elif(file_extension=="mp4"):
        with open(file_path, 'rb') as file:
            with open(thumbnail, 'rb') as photo:
                await update.callback_query.message.reply_video(video=file, filename=clean_filename)
                photo.close()
            file.close()
        
        if os.path.exists(video_filename):
            os.remove(video_filename)
        if os.path.exists(thumbnail):
            os.remove(thumbnail)
        if os.path.exists(file_path):
            os.remove(file_path)


async def get_url(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    context.user_data['url'] = url

    # Перевірка правильності URL
    parsed_url = urlparse(url)
    if parsed_url.scheme and parsed_url.netloc:
        keyboard = [
            [InlineKeyboardButton("Відео", callback_data='mp4'),
             InlineKeyboardButton("Аудіо", callback_data='mp3')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Будь ласка, виберіть формат:', reply_markup=reply_markup)
    else:
        await update.message.reply_text('Невірне посилання. Будь ласка, надішліть коректне посилання.')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text("Use /start to test this bot.")



if __name__ == "__main__":
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_url))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)