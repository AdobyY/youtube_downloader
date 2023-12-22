import os
import re
import json
import time
from urllib.parse import urlparse
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
from telegram import Bot, InputFile
from dotenv import load_dotenv
import logging
from download import download
import time
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Set logging level
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Get the token from environment variable
TOKEN = os.getenv('TOKEN')

# Create a bot instance
bot = Bot(token=TOKEN)

progress_message = None

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Будь ласка, надішліть посилання.')

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    context.user_data['chat_id'] = update.effective_chat.id
    context.user_data['format'] = query.data
    context.user_data['timestamp'] = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    context.user_data['user_id'] = update.effective_user.id
    context.user_data['user_name'] = update.effective_user.first_name + " " + update.effective_user.last_name
    context.user_data['username'] = update.effective_user.username
    context.user_data['url'] = context.user_data.get('url')

    # Збереження даних про користувача та посилання в JSON-файл
    save_user_data(context.user_data)

    file_path, author = download(context.user_data['url'], context.user_data['format'], context)
    print(author)
    if file_path:
        send_file(context.user_data['chat_id'], file_path, author)

        # Close the file before attempting to delete it
        with open(file_path, 'rb') as file:
            file.close()

        # Видалення файлу після відправлення
        os.remove(file_path)
        print(f"File removed: {file_path}")

        video_filename = file_path.rsplit(".", 1)[0] + ".mp4"
        with open(video_filename, 'rb') as file:
            file.close()
        if os.path.exists(video_filename):
            os.remove(video_filename)

        # remove photo
        photo_filename = file_path.rsplit(".", 1)[0] + ".jpg"
        clean_photo_filename = re.sub(r'\s*\[.*?\]', '', photo_filename)
        with open(clean_photo_filename, 'rb') as file:
            file.close()
        if os.path.exists(clean_photo_filename):
            os.remove(clean_photo_filename)
            
    else:
        update.message.reply_text('Невірне посилання. Будь ласка, надішліть коректне посилання.')

def get_url(update: Update, context: CallbackContext) -> None:
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
        update.message.reply_text('Будь ласка, виберіть формат:', reply_markup=reply_markup)
    else:
        update.message.reply_text('Невірне посилання. Будь ласка, надішліть коректне посилання.')

def send_file(chat_id, file_path, author):
    clean_filename = re.sub(r'\s*\[.*?\]', '', file_path)
    photo_name = clean_filename.rsplit(".", 1)[0] + ".jpg"
    file_extension = clean_filename[-3:]

    if(file_extension=="mp3"):
        with open(file_path, 'rb') as file:
            with open(photo_name, 'rb') as photo:
                bot.send_audio(chat_id=chat_id, audio=file, title=clean_filename,
                               filename=clean_filename, thumb=InputFile(photo), performer=author)
                photo.close()
            file.close()
    elif(file_extension=="mp4"):
        with open(file_path, 'rb') as file:
            with open(photo_name, 'rb') as photo:
                bot.send_document(chat_id=chat_id, document=file, filename=clean_filename, thumb=InputFile(photo))
                photo.close()
            file.close()


    
    
    

def save_user_data(user_data):
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

def main() -> None:
    global progress_message

    updater = Updater(bot=bot, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, get_url))
    updater.start_polling()
    updater.idle()

    # Зачекайте, поки останнє повідомлення про прогрес не буде відправлено
    while progress_message is None:
        time.sleep(1)
    progress_message.edit_text("Завантаження завершено!")

if __name__ == '__main__':
    main()
