import os
import requests
from pytube import YouTube
import telebot
import re
import time
from telebot import types

bot = telebot.TeleBot('6437967727:AAHufdo8Ezsbuj7lR74EQn4-trn2voFa6N8')

current_directory = os.getcwd()
video_directory = os.path.join(current_directory, 'video')
image = 'https://i.pinimg.com/736x/e4/01/01/e401012cb58bcde4da7912e5e426a1e5.jpg'

if not os.path.exists(video_directory):
    os.makedirs(video_directory)
    print(f"[INFO] Папку video не найдено, создаю её сам.")


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name

    ms = '''
Привет! Я <b>бот для скачивания короткое видео</b> из YouTube и TikTok.
Просто отправь мне ссылку и я всё <b>быстренько</b> сделаю :)
    '''
    bot.send_photo(message.chat.id, image, parse_mode='html', caption=ms)


@bot.message_handler(func=lambda message: True)
def download_video(message):
    video_path = None
    try:
        video_url = message.text
        if "youtube.com" in video_url or "youtu.be" in video_url:
            video_id = extract_video_id(video_url)
            if video_id:
                yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')
                markup = types.ReplyKeyboardMarkup(row_width=2)
                item_video = types.KeyboardButton('Видео')
                item_audio = types.KeyboardButton('Аудио')
                markup.add(item_video, item_audio)
                msg = bot.send_message(message.chat.id, "Выберите формат загрузки:", reply_markup=markup)
                bot.register_next_step_handler(msg, process_format_choice, yt)
            else:
                bot.send_message(message.chat.id, 'Пожалуйста, отправьте корректную ссылку на видео с YouTube.')
        elif "tiktok.com" in video_url:
            download_and_send_tiktok(video_url, message.chat.id)
        else:
            bot.send_message(message.chat.id, 'Пожалуйста, отправьте корректную ссылку на видео с YouTube или TikTok.')
    except Exception as e:
        print(f'[INFO] Произошла ошибка: {str(e)}')
        bot.reply_to(message, f'Произошла ошибка: {str(e)}')
        if video_path and os.path.exists(video_path):
            os.remove(video_path)


def extract_video_id(url):
    regex = r'(?:v=|\/)([0-9A-Za-z_-]{11})'
    match = re.search(regex, url)
    if match:
        return match.group(1)
    else:
        return None


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


def download_and_send_video(yt, chat_id):
    video_path = download_video_from_youtube(yt)
    send_video(chat_id, video_path)


def download_and_send_audio(yt, chat_id):
    audio_path = download_audio_from_youtube(yt)
    send_audio(chat_id, audio_path)


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


def download_and_send_tiktok(url, chat_id):
    try:
        response = requests.get(f"https://api.snaptik.app/api/v1/link?url={url}")
        response.raise_for_status()  # Raises exception for HTTP errors
        data = response.json()
        if data and "data" in data and data["data"]:
            video_url = data["data"][0]["url"]
            video_data = requests.get(video_url).content

            cleaned_title = re.sub(r'[^\w\s.-]', '', url.split('/')[-1])
            video_filename = f'{cleaned_title}.mp4'
            video_path = os.path.join(video_directory, video_filename)

            with open(video_path, 'wb') as f:
                f.write(video_data)

            send_video(chat_id, video_path)
        else:
            bot.send_message(chat_id, 'Не удалось найти видео на TikTok.')
    except requests.HTTPError as http_err:
        print(f'[INFO] HTTP error occurred: {http_err}')
        bot.send_message(chat_id, f'HTTP error occurred: {http_err}')
    except Exception as e:
        print(f'[INFO] An error occurred while downloading video from TikTok: {str(e)}')
        bot.send_message(chat_id, f'An error occurred while downloading video from TikTok: {str(e)}')


def send_video(chat_id, video_path):
    if os.path.exists(video_path):
        print(f'[INFO] Видео успешно загружено, автоматическое удаление произойдет после отправки видео.')
        bot.send_message(chat_id, 'Видео было загружено на сервер, оно отправится вам через 15 секунд.')
        time.sleep(15)
        bot.send_video(chat_id, video=open(video_path, 'rb'), caption=f'Видео успешно загружено! Держи!')
        os.remove(video_path)
        print(f'[INFO] Видео: {os.path.basename(video_path)}, было удалено с сервера.')
    else:
        bot.send_message(chat_id, 'Видео не было загружено.')


def send_audio(chat_id, audio_path):
    if os.path.exists(audio_path):
        print(f'[INFO] Аудио успешно загружено, автоматическое удаление произойдет после отправки аудио.')
        bot.send_message(chat_id, 'Аудио было загружено на сервер, оно отправится вам через 15 секунд.')
        time.sleep(15)
        bot.send_audio(chat_id, audio=open(audio_path, 'rb'), caption=f'Аудио успешно загружено! Держи!')
        os.remove(audio_path)
        print(f'[INFO] Аудио: {os.path.basename(audio_path)}, было удалено с сервера.')
    else:
        bot.send_message(chat_id, 'Аудио не было загружено.')


bot.polling()
