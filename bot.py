import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import logging
from datetime import datetime

# تنظیم لاگینگ
logging.basicConfig(filename='bot_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

# توکن و تنظیمات
BOT_TOKEN = '8268425583:AAFkSCeYzXAU2gcyz-tZLSwpzVg0uZ061IU'
ADMIN_ID = 7989867522
ADMIN_USERNAME = '@YourAdminUsername'

bot = telebot.TeleBot(BOT_TOKEN)

# آدرس والت
TRC20_WALLET = "TQzZgrHNtG9i8mGufpvW12sxFuy"
BEP20_WALLET = "0x7485e33695b722aA071A868bb6959533a3e449b02E"

# دیتابیس
conn = sqlite3.connect('elite_yield.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance REAL DEFAULT 0,
    total_profit REAL DEFAULT 0,
    level TEXT DEFAULT 'Bronze',
    last_profit_time INTEGER DEFAULT 0,
    referrer_id INTEGER DEFAULT NULL,
    created_at INTEGER DEFAULT 0,
    language TEXT DEFAULT 'en'
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
conn.commit()

# دیکشنری زبان‌ها (کامل, channel حذف شد)
languages = {
    'en': {
        'welcome': """🌟 Welcome to Elite Yield Bot! 🚀

Unlock up to 16% DAILY returns on your USDT investments! 💰

💎 Membership Levels:
• Bronze (10% daily) - $0-$99
• Silver (12% daily) - $100-$499  
• Gold (16% daily) - $500+

💳 Minimum deposit: $10 USDT
🌐 Networks: TRC20 or BEP20

Start earning passive income today! 📈""",
        'balance': """💰 Your Balance: ${balance:.2f} USDT
📈 Total Profit: ${total_profit:.2f} USDT
💎 Level: {level}""",
        'deposit_instructions': """💳 Deposit Instructions:

Send USDT to:
🌐 TRC20: `{TRC20_WALLET}`
🌐 BEP20: `{BEP20_WALLET}`

Min $10. Confirm after sending.""",
        'enter_deposit_amount': 'Enter amount (min $10):',
        'invalid_amount': '❌ Invalid! Min $10.',
        'enter_wallet': 'Enter wallet (TRC20/BEP20):',
        'withdraw_submitted': '✅ Submitted! Wait for admin.',
        'referral_text': """👥 Referral Link: `{ref_link}`
Referrals: {ref_count}
5% commission!""",
        'support': """📞 Support:
👤 Admin: {ADMIN_USERNAME}
🆔 ID: {ADMIN_ID}""",
        'choose_language': 'Choose language:',
        'english': 'English 🇺🇸',
        'persian': 'Persian 🇮🇷',
        'turkish': 'Turkish 🇹🇷',
        'arabic': 'Arabic 🇸🇦'
    },
    # fa, tr, ar مشابه en, channel حذف, کوتاه برای فضا
    'fa': {k: v.replace('Support', 'پشتیبانی').replace('Channel', '') for k, v in languages['en'].items()},
    'tr': {k: v.replace('Support', 'Destek').replace('Channel', '') for k, v in languages['en'].items()},
    'ar': {k: v.replace('Support', 'الدعم').replace('Channel', '') for k, v in languages['en'].items()}
}

def get_level(balance):
    if balance < 100: return 'Bronze', 0.10
    elif balance < 500: return 'Silver', 0.12
    return 'Gold', 0.16

def main_menu(is_admin=False, lang='en'):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add('💰 Balance', '💳 Deposit')
    markup.add('💸 Withdraw', '👥 Referral')
    markup.add('📞 Support')
    if is_admin:
        markup.add('🛠 Admin Panel')
    return markup

def admin_menu(lang='en'):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('👥 Users List', '⏳ Pending Requests')
    markup.add('📊 Statistics', '🔙 Back')
    return markup

def language_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton(languages['en']['english'], callback_data='lang_en'))
    markup.add(InlineKeyboardButton(languages['en']['persian'], callback_data='lang_fa'))
    markup.add(InlineKeyboardButton(languages['en']['turkish'], callback_data='lang_tr'))
    markup.add(InlineKeyboardButton(languages['en']['arabic'], callback_data='lang_ar'))
    return markup

@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"User_{user_id}"
    
    try:
        cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.commit()
    except:
        result = None
    
    lang = result[0] if result else 'en'
    
    if not result:
        cursor.execute('INSERT INTO users (user_id, username, created_at, language) VALUES (?, ?, ?, ?)', (user_id, username, int(datetime.now().timestamp()), 'en'))
        conn.commit()
        bot.send_message(message.chat.id, languages['en']['choose_language'], reply_markup=language_menu())
        return
    
    cursor.execute('UPDATE users SET username = ? WHERE user_id = ?', (username, user_id))
    conn.commit()
    
    is_admin = user_id == ADMIN_ID
    
    try:
        with open('welcome_banner.jpg', 'rb') as banner:
            bot.send_photo(message.chat.id, banner, caption=languages[lang]['welcome'], reply_markup=main_menu(is_admin, lang))
    except FileNotFoundError:
        bot.send_message(message.chat.id, languages[lang]['welcome'], reply_markup=main_menu(is_admin, lang))

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    user_id = message.from_user.id
    try:
        cursor.execute('SELECT balance, total_profit, level, language FROM users WHERE user_id = ?', (user_id,))
        user_data = cursor.fetchone()
        conn.commit()
    except:
        user_data = (0, 0, 'Bronze', 'en')
    
    balance, total_profit, level, lang = user_data or (0, 0, 'Bronze', 'en')
    is_admin = user_id == ADMIN_ID
    
    if message.text == '💰 Balance':
        text = languages[lang]['balance'].format(balance=balance, total_profit=total_profit, level=level)
        bot.send_message(message.chat.id, text, reply_markup=main_menu(is_admin, lang))
    
    elif message.text == '💳 Deposit':
        msg = bot.send_message(message.chat.id, languages[lang]['enter_deposit_amount'])
        bot.register_next_step_handler(msg, lambda m: process_deposit_amount(m, lang))
    
    elif message.text == '💸 Withdraw':
        msg = bot.send_message(message.chat.id, languages[lang]['enter_amount'])
        bot.register_next_step_handler(msg, process_withdraw_request)
    
    elif message.text == '👥 Referral':
        ref_link = f't.me/eliteyieldbot?start=ref_{user_id}'
        cursor.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user_id,))
        ref_count = cursor.fetchone()[0]
        conn.commit()
        text = languages[lang]['referral_text'].format(ref_link=ref_link, ref_count=ref_count)
        bot.send_message(message.chat.id, text, reply_markup=main_menu(is_admin, lang))
    
    elif message.text == '📞 Support':
        text = languages[lang]['support'].format(ADMIN_USERNAME=ADMIN_USERNAME, ADMIN_ID=ADMIN_ID)
        bot.send_message(message.chat.id, text, reply_markup=main_menu(is_admin, lang))
    
    # Admin panel and others (keep from previous, with try/except)
    # ... (admin code with try/except for cursor)
    
    else:
        bot.send_message(message.chat.id, 'Use menu.', reply_markup=main_menu(is_admin, lang))

# بقیه توابع (process_deposit_amount, callback_handler with try, etc.) هم با try/except and conn.commit()

if __name__ == '__main__':
    print("🚀 Starting...")
    bot.polling(none_stop=True)
