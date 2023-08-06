
from telebot import types
from schedule import every
from multiprocessing import Process

import telebot
import datetime
import config
import schedule
import time
import SQL_funcs



bot = telebot.TeleBot(config.SKBT_SECRETARY_TOKEN)

def add_sender(user_id):
    SQL_funcs.SQL_Update('INSERT INTO "secretary"."T_SENDERS" ("TELEGRAM_ID") VALUES (%s);',
                    (user_id,))


def get_not_sended():
    rows = SQL_funcs.SQL_Select('SELECT * FROM secretary."T_USERS" u where u."TELEGRAM_ID" not in (select "TELEGRAM_ID" from secretary."T_SENDERS" s)', ())
    return rows

def get_user(user_id):
    row = SQL_funcs.SQL_Select('select * from "secretary"."T_USERS" u where u."TELEGRAM_ID" = %s', (user_id,))
    return row

def get_users():
    rows = SQL_funcs.SQL_Select('select * from "secretary"."T_USERS"', ())
    
    return rows


def set_silenced(user_id, switch):
    SQL_funcs.SQL_Update('UPDATE secretary."T_USERS" SET "SILENCED" = %s WHERE "TELEGRAM_ID" = %s;', (switch, user_id))

def get_bosses():
    rows = SQL_funcs.SQL_Select('SELECT * FROM secretary."T_USERS" u where u."IS_BOSS" is true;', ())
    return rows


# функция отправки сообщения с выбором места работы
def send_choice(user_id):
    user = get_user(user_id)[0]
    #print(user)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    ofice_btn = types.KeyboardButton("💼 Офис")
    dist_btn = types.KeyboardButton("🏡 Удаленно")
    off_btn = types.KeyboardButton("🚫 Выключить")
    on_btn = types.KeyboardButton("✅ Включить")
    canсel_btn = types.KeyboardButton("🔚 Отмена")
    if (user['SILENCED']):
        markup.add(ofice_btn, dist_btn, on_btn, canсel_btn)
    else:
        markup.add(ofice_btn, dist_btn, off_btn, canсel_btn)
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
            rows = get_not_sended()
            for row in rows:
                if (now.hour == 9 + 7 - row['UTC_DIFF']):
                    if (not row['SILENCED']):
                        send_choice(row['TELEGRAM_ID'])



def is_send_reset():
    SQL_funcs.SQL_Update('delete from "secretary"."T_SENDERS"', ())
    

def send_report():
    now = datetime.datetime.now() 
    if (now.weekday() < 5):
        not_senders = get_not_sended()
        report_str = ''
        for not_sender in not_senders:
            if (not_sender['TELEGRAM_ID'] != 366612076):
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
    
    @bot.message_handler(commands=['menu'])
    def send_workplace(message):
         send_choice(message.from_user.id)
    
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

        elif (message.text == '🚫 Выключить'):
            set_silenced(message.from_user.id, True)
            bot.send_message(message.from_user.id, 'Рассылка для вас отключена.', reply_markup=types.ReplyKeyboardRemove())

        elif (message.text == '✅ Включить'):
            set_silenced(message.from_user.id, False)
            bot.send_message(message.from_user.id, 'Рассылка для вас включена.', reply_markup=types.ReplyKeyboardRemove())   
        elif (message.text == '🔚 Отмена'):
            bot.send_message(message.from_user.id, 'Ничего не произошло :)', reply_markup=types.ReplyKeyboardRemove())

    bot.infinity_polling(none_stop=True)
           


