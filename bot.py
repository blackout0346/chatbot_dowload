import os
import requests
from pytube import YouTube
import telebot
import re
import time
from telebot import types
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import VideoFileClip

bot = telebot.TeleBot('6437967727:AAHufdo8Ezsbuj7lR74EQn4-trn2voFa6N8')

current_directory = os.getcwd()
video_directory = os.path.join(current_directory, 'video')
image = 'https://i.pinimg.com/736x/e4/01/01/e401012cb58bcde4da7912e5e426a1e5.jpg'

if not os.path.exists(video_directory):
    os.makedirs(video_directory)
    print(f"[INFO] Папку video не найдено, создаю её сам.")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    ms = '''
Привет! Я <b>бот для скачивания shorts и видео</b> из YouTube.
Просто отправь мне ссылку и я всё <b>быстренько</b> сделаю :)
    '''
    bot.send_photo(message.chat.id, image, parse_mode='html', caption=ms)

@bot.message_handler(func=lambda message: True)
def download_video(message):
    try:
        video_url = message.text
        if "youtube.com" in video_url or "youtu.be" in video_url:
            yt = YouTube(video_url)
            ask_format_choice(message, yt)
        elif "tiktok.com" in video_url:
            download_and_send_tiktok(video_url, message.chat.id)
        else:
            bot.send_message(message.chat.id, 'Пожалуйста, отправьте корректную ссылку на видео с YouTube.')
    except Exception as e:
        print(f'[INFO] Произошла ошибка: {str(e)}')
        bot.reply_to(message, f'Произошла ошибка: {str(e)}')

def ask_format_choice(message, yt):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Видео', 'Аудио')
    msg = bot.reply_to(message, 'Что вы хотите скачать?', reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: process_format_choice(m, yt))

def process_format_choice(message, yt):
    try:
        chat_id = message.chat.id
        user_choice = message.text.lower()

        if user_choice == 'видео':
            download_and_send_video(yt, chat_id)
        elif user_choice == 'аудио':
            download_and_send_audio(yt, chat_id)
        else:
            bot.send_message(chat_id, 'Пожалуйста, выберите формат, используя клавиатуру.')
    except Exception as e:
        print(f'[INFO] Ошибка при обработке выбора формата: {str(e)}')
        bot.send_message(chat_id, f'Произошла ошибка: {str(e)}')

def download_video_from_youtube(yt):
    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    cleaned_title = re.sub(r'[^\w\s.-]', '', yt.title)
    video_filename = f'{cleaned_title}.mp4'
    video_path = os.path.join(video_directory, video_filename)
    stream.download(output_path=video_directory, filename=video_filename)
    return video_path

def download_audio_from_youtube(yt):
    audio_stream = yt.streams.filter(only_audio=True).first()
    cleaned_title = re.sub(r'[^\w\s.-]', '', yt.title)
    audio_filename = f'{cleaned_title}.mp3'
    audio_path = os.path.join(video_directory, audio_filename)
    audio_stream.download(output_path=video_directory, filename=audio_filename)
    return audio_path

def split_video(video_path, max_size=50 * 1024 * 1024):
    video = VideoFileClip(video_path)
    duration = video.duration  # продолжительность видео в секундах
    parts = []
    part_num = 1
    current_start = 0

    # Рассчитываем среднее время для одного 50 МБ чанка
    file_size = os.path.getsize(video_path)
    chunk_duration = (max_size / (file_size / duration))

    while current_start < duration:
        part_filename = f'{os.path.splitext(video_path)[0]}_part{part_num}.mp4'
        current_end = min(current_start + chunk_duration, duration)
        ffmpeg_extract_subclip(video_path, current_start, current_end, targetname=part_filename)
        parts.append(part_filename)
        current_start = current_end
        part_num += 1

        # Проверяем размер полученного файла
        if os.path.getsize(part_filename) > max_size:
            print(f'[WARNING] Часть {part_filename} превышает 50 МБ. Разделение видео может быть некорректным.')
            break

    video.close()
    return parts

def send_video_parts(chat_id, video_parts):
    for part in video_parts:
        with open(part, 'rb') as video:
            bot.send_video(chat_id, video)
        os.remove(part)

def download_and_send_video(yt, chat_id):
    video_path = download_video_from_youtube(yt)
    if os.path.getsize(video_path) > 50 * 1024 * 1024:  # 50 MB
        video_parts = split_video(video_path)
        send_video_parts(chat_id, video_parts)
    else:
        send_media(chat_id, video_path, is_video=True)

def download_and_send_audio(yt, chat_id):
    audio_path = download_audio_from_youtube(yt)
    send_media(chat_id, audio_path, is_video=False)

def download_and_send_tiktok(url, chat_id):
    try:
        response = requests.get(f"https://api.snaptik.app/api/v1/link?url={url}")
        response.raise_for_status()
        data = response.json()
        if data and "data" in data and data["data"]:
            video_url = data["data"][0]["url"]
            video_data = requests.get(video_url).content

            cleaned_title = re.sub(r'[^\w\s.-]', '', url.split('/')[-1])
            video_filename = f'{cleaned_title}.mp4'
            video_path = os.path.join(video_directory, video_filename)

            with open(video_path, 'wb') as f:
                f.write(video_data)

            if os.path.getsize(video_path) > 10 * 1024 * 1024:  # 50 MB
                video_parts = split_video(video_path)
                send_video_parts(chat_id, video_parts)
            else:
                send_media(chat_id, video_path, is_video=True)
        else:
            bot.send_message(chat_id, 'Не удалось найти видео на TikTok.')
    except requests.HTTPError as http_err:
        print(f'[INFO] HTTP error occurred: {http_err}')
        bot.send_message(chat_id, f'HTTP error occurred: {http_err}')
    except Exception as e:
        print(f'[INFO] An error occurred while downloading video from TikTok: {str(e)}')
        bot.send_message(chat_id, f'An error occurred while downloading video from TikTok: {str(e)}')

def send_media(chat_id, media_path, is_video=True):
    if os.path.exists(media_path):
        print(f'[INFO] Медиа успешно загружено, автоматическое удаление произойдет после отправки медиа.')
        bot.send_message(chat_id, 'Медиа было загружено на сервер. Это может занять несколько секунд (или минут, если оно большое).')
        time.sleep(15)
        if is_video:
            bot.send_video(chat_id, video=open(media_path, 'rb'), caption='Видео успешно загружено! Держи!')
        else:
            bot.send_audio(chat_id, audio=open(media_path, 'rb'), caption='Аудио успешно загружено! Держи!')
        os.remove(media_path)
        print(f'[INFO] Медиа: {os.path.basename(media_path)}, было удалено с сервера.')
    else:
        bot.send_message(chat_id, 'Медиа не было загружено.')

bot.polling()
