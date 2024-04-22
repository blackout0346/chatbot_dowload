import logging
from aiogram import Bot
from aiogram import Dispatcher
from aiogram import executor
from aiogram import types
import ytttb

api_tok = 'TOKEN'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=api_tok)
dp = Dispatcher(bot)
link = ''


@dp.message_handler(commands=['start'])
async def welcome(message: types.Message):
    await  message.reply('Пришли ссылку')


@dp.message_handler()
async def buttns(message: types.Message):
    link = message.text
    kb = [
        [types.KeyboardButton(text="Video")],
        [types.KeyboardButton(text="Audio")],
        [types.KeyboardButton(text="Thumbnail")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb)
    await message.answer('Choose the action', reply_markup=keyboard)
    return link


@dp.message_handler(text='Video')
async def vids(message: types.Message):
    await bot.send_video(message.chat.id, open(str(ytttb.send_me_vid(link=link, r='h')), 'rb'))


@dp.message_handler(text='Audio')
async def audio(message: types.Message):
    await bot.send_video(message.chat.id, open(str(ytttb.send_me_audio(link))))


@dp.message_handler(text='Thumbnail')
async def tmb(message: types.Message):
    await message.answer(ytttb.send_me_pic(link))


executor.start_polling(dp, skip_updates=True)