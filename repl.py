import os
import re
import time
import logging
from download import download
from datetime import datetime
from urllib.parse import urlparse
from telegram import (Update, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (filters, Application, ContextTypes, MessageHandler,
                          CommandHandler, CallbackContext,
                          CallbackQueryHandler)
from response_to_user.chatbot import get_response

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
  d = f"{user_data['timestamp']} - {user_data['user_name']} {user_data['username']}: {user_data['format']} - {user_data['url']} \n"
  print(d)
  with open('user_data.txt', 'a', encoding='utf8') as f:
    f.write(d)


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
            video=file, filename=video)
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
  if os.path.exists(video.replace('.mp4', '.webm')):
    os.remove(video.replace('.mp4', '.webm'))


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
    await reply_to_user(update)


async def reply_to_user(update):
  message = update.message.text
  response = get_response(message)
  log_message = f'{update.effective_user.username} {update.effective_user.first_name} {update.effective_user.last_name}:  "{message} - {response}" {datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")}'

  print(log_message)
  with open('conversation.txt', 'a', encoding='utf8') as f:
    f.write(log_message + '\n')

  await update.message.reply_text(response)


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
