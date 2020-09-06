import sqlite3
import telebot
import datetime
import time
import schedule
from threading import Thread
import logging

logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

bot = telebot.TeleBot("TOKEN") #Взять у @BotFather
db = sqlite3.connect('base.db', check_same_thread=False) #База данных (можно сделать и на гуглдоксах, но зачем?)
c = db.cursor()

c.execute("create table if not exists today (name str)")
c.execute("create table if not exists tomorrow (name str)") #Если нет таблиц, то будут
db.commit()

chat_id = "ID" #Айди чата - можно взять у @combot (рекомендую использовать), когда зайдёте в панель, в ссылке будет длинное число с минусом, или без, вставляете его в кавычки

def send_all(table = "today", chat_id = chat_id): #отправить за *указать день*
	
	if table in ['today', 'tomorrow']:
		try:
			c.execute("select name from {}".format(table))
			all_resp = c.fetchall()
		except sqlite3.OperationalError:
			print('Виталик, база пустая, придумай тут что-то')
			logging.error('empty base (remove and start all over)')
			return

	else:
		logging.error('send_all invalid table value ({})'.format(table))
		return

	if table == 'today':
		msg = 'Расписание на сегодня\n'
	else:
		msg = 'Расписание на завтра\n'
	for x in all_resp:
		msg += "\n{}. <b>{}</b>".format(all_resp.index(x)+1, ''.join(c for c in x if c not in "(',)" )) #пример использования парс мода (смотри дальше)

	bot.send_message(chat_id, msg, parse_mode = "HTML") #или MARKDOWN, что удобнее

@bot.message_handler(regexp = 'Всё сегодня')
def req_td(message):

	if message.text.lower() == 'всё сегодня':

		send_all('today', message.chat.id)

@bot.message_handler(regexp = 'Всё завтра')
def req_tom(message):

	if message.text.lower() == 'всё завтра':

		send_all('tomorrow', message.chat.id) #Вообще можно что угодно писать, но так красивее :)

@bot.message_handler(commands = ['upd_tm'])
def upd_tm(message):

	if message.text == '/upd_tm':
		msg = bot.reply_to(message, 'Окей, отправь следущим сообщением расписание на завтра!\n\nФормат такой:\nПредмет №1\nПредмет №2\nПредмет №3\nПредмет №4\n\nЕсли пары нет - ставь прочерк')
		bot.register_next_step_handler(msg, upd_tm_rec)
	else:
		if len(message.text.split('\n')) == 5:
			a = message.text.split('\n')[1:5]
			print(a)
			c.execute("delete from tomorrow")
			for x in a:
				c.execute("insert into tomorrow (name) values ('{}')".format(x))
			db.commit()
		else:
			bot.reply_to(message, 'Что-то не то ты мне пишешь, ещё разок!')

def upd_tm_rec(message): ###Если не написать сразу задания, то это - продолжение

	if len(message.text.split('\n')) == 4:
			a = message.text.split('\n')
			print(a)
			c.execute("delete from tomorrow")
			for x in a:
				c.execute("insert into tomorrow (name) values ('{}')".format(x))
			db.commit()
	else:
		bot.reply_to(message, 'Что-то не то ты мне пишешь, ещё разок!')

def swap(): ##Смена дней (завтра остаётся, сегодня = завтра)

	c.execute("select * from tomorrow")
	tom = c.fetchall()
	c.execute("delete from today")
	for x in tom:
		c.execute("insert into today ('name') values ('{}')".format(''.join(c for c in x if c not in "(',)" )))
	db.commit()


class MTread(Thread):
	def __init__(self, name):
		Thread.__init__(self)
		self.name = name
	def run(self):
		print(datetime.datetime.today().weekday())
		schedule.every().day.at("06:50").do(send_all, 'today') ##Второе значение - аргументы, третье - кварги
		schedule.every().day.at("17:30").do(send_all, 'tomorrow')
		schedule.every().day.at("23:59").do(swap)
		while True:
			schedule.run_pending()
			time.sleep(1)
name = 'schedule_thr'
schedthr = MTread(name)
schedthr.start()

bot.polling() #Или на вебхуках (см примеры pyTelegramBotAPI)
