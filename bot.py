import config
import logging
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, executor, types
from sqlighter import SQLighter

from stopgame import StopGame

# задаем уровень логов
logging.basicConfig(level=logging.INFO)

# инициализируем бота
bot = Bot(token="1669212784:AAG7bd094ih3mlsRNYbMqwSc_T5ig34Pp00")
dp = Dispatcher(bot)

# инициализируем соединение с БД
db = SQLighter('db_bot_parsing.db')

# инициализируем парсер
sg = StopGame('lastkey.txt')

# Реагирование на /start
@dp.message_handler(commands=['start'])
async def subscribe(message: types.Message):
	await message.answer("Добро пожаловать!\nПодписавшись, ты будешь получать уведомления о\
		всех вышедших обзорах с сайта StopGame.\nВ случае отписки я очень расстроюсь и перестану присылать тебе видосики(( ")

# Команда активации подписки
@dp.message_handler(commands=['subscribe'])
async def subscribe(message: types.Message):
	if(not db.subscriber_exists(message.from_user.id)):
		# если юзера нет в базе, добавляем его
		db.add_subscriber(message.from_user.id)
	else:
		# если он уже есть, то просто обновляем ему статус подписки
		db.update_subscription(message.from_user.id, True)
	
	await message.answer("Вы успешно подписались на рассылку!\nЖдите, скоро выйдут новые обзоры и вы узнаете о них первыми =)")

# Команда отписки
@dp.message_handler(commands=['unsubscribe'])
async def unsubscribe(message: types.Message):
	if(not db.subscriber_exists(message.from_user.id)):
		# если юзера нет в базе, добавляем его с неактивной подпиской (запоминаем)
		db.add_subscriber(message.from_user.id, False)
		await message.answer("Вы и так не подписаны.")
	else:
		# если он уже есть, то просто обновляем ему статус подписки
		db.update_subscription(message.from_user.id, False)
		await message.answer("Вы успешно отписаны от рассылки.")

@dp.message_handler(commands=['statistics'])
async def get_statistics(message: types.Message):
	if(message.from_user.id == 493872975):
		subscriptions = db.get_subscriptions_all()
		await message.answer("Пользователи в базе данных:\n" + '\n'.join(map(str, subscriptions)))
	else:
	    await message.answer("Нет прав на выполнение запроса")


# проверяем наличие новых игр и делаем рассылки
async def scheduled(wait_for):
	while True:
		await asyncio.sleep(wait_for)

		# проверяем наличие новых игр
		new_games = sg.new_games()

		if(new_games):
			# если игры есть, переворачиваем список и итерируем
			new_games.reverse()
			for ng in new_games:
				# парсим инфу о новой игре
				nfo = sg.game_info(ng)

				# получаем список подписчиков бота
				subscriptions = db.get_subscriptions()

				# отправляем всем новость
				for s in subscriptions:
					with open(sg.download_image(nfo['image']), 'rb') as photo:
						await bot.send_photo(
							s[1],
							photo,
							caption = nfo['title'] + "\n" + "Оценка: " + nfo['score'] + "\n"  + nfo['link'],
							#caption = nfo['title'] + "\n" + "Оценка: " + nfo['score'] + "\n" + nfo['excerpt'] + "\n\n" + nfo['link'],
							disable_notification = True
						)
						
				
				# обновляем ключ
				sg.update_lastkey(nfo['id'])





# запускаем лонг поллинг
if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	loop.create_task(scheduled(10))  # проверка через каждые 10 сек 
	executor.start_polling(dp, skip_updates=True)