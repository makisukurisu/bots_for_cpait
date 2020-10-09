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

c.execute('CREATE TABLE if not exists "tomorrow" ("pair_n"	int NOT NULL, CONSTRAINT "td_ref" FOREIGN KEY("pair_n") REFERENCES tasks)')
c.execute('CREATE TABLE if not exists "today" ("pair_n"	int NOT NULL, CONSTRAINT "td_ref" FOREIGN KEY("pair_n") REFERENCES tasks)')
c.execute('CREATE TABLE if not exists "tasks" ("pair_n"	INTEGER NOT NULL UNIQUE,"pair_name"	str NOT NULL,"task"	str NOT NULL,PRIMARY KEY("pair_n" AUTOINCREMENT))') #Если нет таблиц, то будут
db.commit()

chat_id = "ID" #Айди чата - можно взять у @combot (рекомендую использовать), когда зайдёте в панель, в ссылке будет длинное число с минусом, или без, вставляете его в кавычки

def send_all(table = "today", chat_id = chat_id): #отправить за *указать день*
	
	if table in ['today', 'tomorrow']:
		try:
			c.execute("select * from tasks where pair_n in {}".format(table))
			tasks = c.fetchall()
			c.execute("select * from {}".format(table))
			temp = c.fetchall()
			tasks = [x for _, x in sorted(zip(temp, tasks), key=lambda pair: pair[0])]
			print(tasks)
		except Exception as E:
			logging.error('Empty base (start all over?) ({})'.format(E))
			return
	else:
		logging.error('send_all invalid table value ({})'.format(table))
		return

	if table == 'today':
		msg = 'Расписание на сегодня\n'
	else:
		msg = 'Расписание на завтра\n'
	for x in range(len(tasks)):
		msg += "\n{}. <b>{}</b> - {}".format(x+1, tasks[x][1], tasks[x][2]) #пример использования парс мода (смотри дальше)

	bot.send_message(chat_id, msg, parse_mode = "HTML") #или MARKDOWN, что удобнее

@bot.message_handler(regexp = 'Всё сегодня')
def req_td(message):

	if message.text.lower() == 'всё сегодня':

		send_all('today', message.chat.id)

@bot.message_handler(regexp = 'Всё завтра')
def req_tom(message):

	if message.text.lower() == 'всё завтра':

		send_all('tomorrow', message.chat.id)

@bot.message_handler(commands = ['upd_tm'])
def upd_tm(message):

	if message.text == '/upd_tm':
		msg = bot.reply_to(message, 'Окей, отправь следущим сообщением расписание на завтра!\n\nФормат такой:\nПредмет №1\nПредмет №2\nПредмет №3\nПредмет №4\n\nЕсли пары нет - ставь прочерк')
		bot.register_next_step_handler(msg, upd_tm_rec)
	else:
		if len(message.text.split('\n')) == 5:
			a = message.text.split('\n')[1:5]
			c.execute("delete from tomorrow")
			c.execute("select pair_n, pair_name from tasks")
			res = c.fetchall()
			for x in a:
				try:
					for z in range(len(res)):
						if x == res[z][1]:
							c.execute("insert into tomorrow (pair_n) values ('{}')".format(res[z][0]))
							raise(SyntaxError)
				except SyntaxError:
					continue
				try:
					c.execute("insert into tasks (pair_name, task) values ('{}', 'None')".format(x))
					c.execute("insert into tomorrow (pair_n) values ((select pair_n from tasks where pair_name = '{}'))".format(x))
				except Exception as E:
					print(E)
			db.commit()
		else:
			bot.reply_to(message, 'Что-то не то ты мне пишешь, ещё разок!')

def upd_tm_rec(message): ###Если не написать сразу задания, то это - продолжение

	if len(message.text.split('\n')) == 4:
		a = message.text.split('\n')
		c.execute("delete from tomorrow")
		c.execute("select pair_n, pair_name from tasks")
		res = c.fetchall()
		for x in a:
			try:
				for z in range(len(res)):
					if x == res[z][1]:
						c.execute("insert into tomorrow (pair_n) values ('{}')".format(res[z][0]))
						raise(SyntaxError)
			except SyntaxError:
				continue
			try:
				c.execute("insert into tasks (pair_name, task) values ('{}', 'None')".format(x))
				c.execute("insert into tomorrow (pair_n) values ((select pair_n from tasks where pair_name = '{}'))".format(x))
			except Exception as E:
				print(E)
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
