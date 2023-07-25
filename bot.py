
from telebot import types
from schedule import every
from multiprocessing import Process

import telebot
import datetime
import config
import schedule
import time
import multiprocessing as mp
import json
import psycopg2
from psycopg2.extras import DictCursor



bot = telebot.TeleBot(config.SKBT_SECRETARY_TOKEN)

def add_sender(user_id):
    conn = psycopg2.connect(dbname = config.DB_NAME, user = config.DB_USER, 
                        password = config.DB_PASSWORD, host = config.DB_HOST)
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute('INSERT INTO "secretary"."T_SENDERS" ("TELEGRAM_ID") VALUES (%s);',
                    (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

def get_not_sended():
    conn = psycopg2.connect(dbname = config.DB_NAME, user = config.DB_USER, 
                        password = config.DB_PASSWORD, host = config.DB_HOST)
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute('SELECT u."NAME" FROM secretary."T_USERS" u where u."TELEGRAM_ID" not in (select "TELEGRAM_ID" from secretary."T_SENDERS" s)')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def get_user(user_id):
    conn = psycopg2.connect(dbname = config.DB_NAME, user = config.DB_USER, 
                        password = config.DB_PASSWORD, host = config.DB_HOST)
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute('select * from "secretary"."T_USERS" u where u."TELEGRAM_ID" = %s', (user_id,))
    row = cursor.fetchall()
    cursor.close()
    conn.close()
    return row

def get_users():
    conn = psycopg2.connect(dbname = config.DB_NAME, user = config.DB_USER, 
                        password = config.DB_PASSWORD, host = config.DB_HOST)
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute('select * from "secretary"."T_USERS"')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def set_silenced(user_id, switch):
    conn = psycopg2.connect(dbname = config.DB_NAME, user = config.DB_USER, 
                        password = config.DB_PASSWORD, host = config.DB_HOST)
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute('UPDATE secretary."T_USERS" SET "SILENCED" = %s WHERE "TELEGRAM_ID" = %s;', (switch, user_id))
    conn.commit()
    cursor.close()
    conn.close()

# функция отправки сообщения с выбором места работы
def send_choice(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    ofice_btn = types.KeyboardButton("💼 Офис")
    dist_btn = types.KeyboardButton("🏡 Удаленно")
    not_disturb_btn = types.KeyboardButton("🚫 Не беспокоить")
    canсel_btn = types.KeyboardButton("🔚 Отмена")
    markup.add(ofice_btn, dist_btn, not_disturb_btn, canсel_btn)
    bot.send_message(user_id, 'Где сегодня работаешь?', reply_markup=markup)
    return 0

def start_schedule():

    every().minute.do(r)
    every().day.at("00:00").do(is_send_reset)   
    every().day.at("13:00").do(send_report)   
   

     
    while (True):
        schedule.run_pending()
        time.sleep(1)

def r():
    now = datetime.datetime.now() 
    if (now.weekday() < 5):
        if (now.minute == 0):
            rows = get_users()
            for row in rows:
                if (now.hour == 9 + 7 - row['UTC_DIFF']):
                    if (not row['SILENCED']):
                        send_choice(row['TELEGRAM_ID'])

            if (now.hour == 13):
                send_report()

def is_send_reset():
    conn = psycopg2.connect(dbname = config.DB_NAME, user = config.DB_USER, 
                        password = config.DB_PASSWORD, host = config.DB_HOST)
    cursor = conn.cursor()
    cursor.execute('delete from "secretary"."T_SENDERS"')
    conn.commit()
    cursor.close()
    conn.close()

def send_report():
    now = datetime.datetime.now() 
    if (now.weekday() < 5):
        not_senders = get_not_sended()
        report_str = ''
        for not_sender in not_senders:
            report_str = report_str + not_sender['NAME'] + "\n"
        bot.send_message(1907932520, "Пользователи, не сообщившие о месте работы сегодня:\n" + report_str)
        bot.send_message(366612076, "Пользователи, не сообщившие о месте работы сегодня:\n" + report_str)

if __name__ == '__main__':
    

    p = Process(target=start_schedule)
    p.start()


    #send_choice('500404357')
    @bot.message_handler(commands=['reset'])
    def reset_command(message):
        is_send_reset()
    
    @bot.message_handler(commands=['start'])
    def start(message):
        bot.send_message(1907932520, str(message.from_user.id) + ' ' + str(message.from_user.first_name) + ' ' + str(message.from_user.last_name))
        #print(message)
    
    @bot.message_handler(commands=['workplace'])
    def send_workplace(message):
         send_choice(message.from_user.id)
    
    @bot.message_handler(commands=['on_work'])
    def anable_work(message):
        set_silenced(message.from_user.id, False)
        bot.send_message(message.from_user.id, 'Вы снова включены в рассылку!')
    
    @bot.message_handler(commands=['u'])
    def repeater(message):
        bot.send_message(1907932520, message.from_user.id)
        send_report()
    
    @bot.message_handler(content_types=['text'])
    def choice_response(message):
        user = get_user(message.from_user.id)
        now_date = datetime.datetime.now().strftime("%d.%m.%Y")
        if (message.text == '💼 Офис' or message.text == '🏡 Удаленно'):
            add_sender(message.from_user.id)
            bot.send_message(message.from_user.id, 'Сообщение отправлено в чат!', reply_markup=types.ReplyKeyboardRemove())
            bot.send_message(config.SKB_CHAT_ID, f"{user[0]['NAME']}\n{now_date} {message.text} #работа", reply_markup=types.ReplyKeyboardRemove())

        elif (message.text == '🚫 Не беспокоить'):
            set_silenced(message.from_user.id, True)
            bot.send_message(message.from_user.id, 'Рассылка для вас отключена. Чтобы включить ее заново, введите команду /on_work', reply_markup=types.ReplyKeyboardRemove())
        elif (message.text == '🔚 Отмена'):
            bot.send_message(message.from_user.id, 'Ничего не произошло :)', reply_markup=types.ReplyKeyboardRemove())

    bot.infinity_polling(none_stop=True)
           


