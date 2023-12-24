import os
import re
import json
import time
import logging
from download import download
from datetime import datetime
from urllib.parse import urlparse
from telegram import (Update, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (filters, Application, ContextTypes, MessageHandler,
                          CommandHandler, CallbackContext,
                          CallbackQueryHandler)

from keep_alive import keep_alive

keep_alive()

TOKEN = os.environ['BOT_API']

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  await update.message.reply_text("Надішліть своє посилання")


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  await update.callback_query.answer()

  context.user_data['chat_id'] = update.effective_chat.id
  context.user_data['format'] = update.callback_query.data
  context.user_data['timestamp'] = datetime.fromtimestamp(
      time.time()).strftime('%Y-%m-%d %H:%M:%S')
  context.user_data['user_id'] = update.effective_user.id
  context.user_data[
      'user_name'] = f'{update.effective_user.first_name} {update.effective_user.last_name}'
  context.user_data['username'] = update.effective_user.username
  context.user_data['url'] = context.user_data.get('url')

  await save_user_data(context.user_data)

  try:
    file_path, author, thumbnail = await download(update, context)
    await update.callback_query.edit_message_text(text="Надсилаю...")
    if file_path:
      await send_file(file_path, author, thumbnail, update)
    else:
      await update.message.reply_text('Тут якась проблемка')

  except Exception:
    await update.callback_query.edit_message_text(text="Щось пішло не так...")


async def save_user_data(user_data):
  json_file_path = 'user_data.json'

  if not os.path.exists(json_file_path):
    data = {}
  else:
    with open(json_file_path, 'r') as file:
      data = json.load(file)

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

  with open(json_file_path, 'w') as file:
    json.dump(data, file, indent=2)


async def send_file(audio, author, thumbnail, update):
  clean_filename = re.sub(r'\s*\[.*?\]', '', audio)
  video = audio.rsplit(".", 1)[0] + ".mp4"
  file_extension = clean_filename[-3:]

  if (file_extension == "mp3"):
    with open(audio, 'rb') as file:
      with open(thumbnail, 'rb') as photo:
        await update.callback_query.message.reply_audio(audio=audio,
                                                        title=clean_filename,
                                                        thumbnail=thumbnail,
                                                        performer=author)
        photo.close()
      file.close()

    remove_files(video, thumbnail, audio)

  else:
    with open(audio, 'rb') as file:
      with open(thumbnail, 'rb') as photo:
        await update.callback_query.message.reply_video(
            video=file, filename=clean_filename.replace(".webm", ".mp4"))
        photo.close()
      file.close()

    remove_files(video, thumbnail, audio)


def remove_files(video, thumbnail, audio):
  if os.path.exists(thumbnail):
    os.remove(thumbnail)
  if os.path.exists(audio):
    os.remove(audio)
  if os.path.exists(video):
    os.remove(video)
  if os.path.exists(video.replace(".mp4", ".webm")):
    os.remove(video.replace(".mp4", ".webm"))


async def get_url(update: Update, context: CallbackContext) -> None:
  url = update.message.text
  context.user_data['url'] = url

  parsed_url = urlparse(url)
  if parsed_url.scheme and parsed_url.netloc:
    keyboard = [[
        InlineKeyboardButton("Відео", callback_data='mp4'),
        InlineKeyboardButton("Аудіо", callback_data='mp3')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Будь ласка, виберіть формат:',
                                    reply_markup=reply_markup)
  else:
    await update.message.reply_text('Ти впевнений, що це правильне посилання?')


async def help_command(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> None:
  await update.message.reply_text("Use /start to test this bot.")


if __name__ == "__main__":
  application = Application.builder().token(TOKEN).build()

  application.add_handler(CommandHandler("start", start))
  application.add_handler(CallbackQueryHandler(button))
  application.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, get_url))

  application.run_polling(allowed_updates=Update.ALL_TYPES)
