import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import threading
import time
import logging
from datetime import datetime

logging.basicConfig(filename='bot_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

# ====== IMPORTANT ======
# Replace 'YOUR_BOT_TOKEN_HERE' with your new bot token (regenerate it now if the old one was exposed).
BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'
# =======================

# Put your admin ID (int). If you exposed it publicly, it's okay but token is critical to rotate.
ADMIN_ID = 7989867522
ADMIN_USERNAME = '@YourAdminUsername'

bot = telebot.TeleBot(BOT_TOKEN)

TRC20_WALLET = "TQzZgrHNtG9i8mGufpvW12sxFuy"
BEP20_WALLET = "0x7485e33695b722aA071A868bb6959533a3e449b02E"

# use a single connection (check_same_thread=False allows threads)
conn = sqlite3.connect('elite_yield.db', check_same_thread=False)

def get_cursor():
    return conn.cursor()

# create tables
cursor = get_cursor()
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

# languages dict (kept as you had)
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
        'deposit_btn': 'Deposit',
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

از امروز درآمد غیرفعال کسب کنید! 📈""",
        'balance_btn': 'موجودی',
        'deposit_btn': 'واریز',
        'withdraw_btn': 'برداشت',
        'referral_btn': 'رفرال',
        'support_btn': 'پشتیبانی',
        'admin_btn': 'پنل ادمین',
        'support_tickets_btn': 'تیکت‌های پشتیبانی',
        'balance': """موجودی شما: ${balance:.2f} USDT
سود کل: ${total_profit:.2f} USDT
سطح: {level}""",
        'deposit_instructions': """دستورالعمل واریز:

USDT را به:
TRC20: `{TRC20_WALLET}`
BEP20: `{BEP20_WALLET}`

حداقل 10$. پس از ارسال تأیید کنید.""",
        'enter_amount': 'مبلغ را وارد کنید (حداقل 10$):',
        'invalid_amount': 'نامعتبر!',
        'confirm_deposit': 'تأیید ${amount}',
        'withdraw_submitted': 'درخواست برداشت ثبت شد! منتظر ادمین.',
        'referral_text': """لینک رفرال شما:
`{ref_link}`

رفرال‌ها: {ref_count}
10% L1, 8% L2, 3% L3 کمیسیون!""",
        'support': 'پیام خود را به پشتیبانی بفرستید:',
        'choose_language': 'زبان انتخاب کنید:',
        'english': 'English',
        'persian': 'فارسی',
        'turkish': 'Türkçe',
        'arabic': 'العربية',
        'daily_profit': 'سود روزانه اضافه شد: ${profit:.2f} ({rate}% نرخ)!\nموجودی جدید: ${new_balance:.2f}'
    },
    'tr': {
        'welcome': """Elite Yield Bot'a Hoş Geldiniz! 🚀

USDT yatırımlarınızda günlük %21.7'ye kadar getiri kilidini açın! 💰

Yatırım bazlı seviyeler:
• $10-99: %16.6
• $100-799: %17.9  
• $800-2399: %19.6
• $2400-5999: %21.7

Min yatırım: $10 USDT
Ağlar: TRC20 veya BEP20

Bugün pasif gelir kazanmaya başlayın! 📈""",
        'balance_btn': 'Bakiye',
        'deposit_btn': 'Yatırım',
        'withdraw_btn': 'Çekim',
        'referral_btn': 'Referans',
        'support_btn': 'Destek',
        'admin_btn': 'Admin Paneli',
        'support_tickets_btn': 'Destek Biletleri',
        'balance': """Bakiyeniz: ${balance:.2f} USDT
Toplam Kar: ${total_profit:.2f} USDT
Seviye: {level}""",
        'deposit_instructions': """Yatırım Talimatları:

USDT'yi gönderin:
TRC20: `{TRC20_WALLET}`
BEP20: `{BEP20_WALLET}`

Min $10. Gönderdikten sonra onaylayın.""",
        'enter_amount': 'Miktarı girin (min $10):',
        'invalid_amount': 'Geçersiz!',
        'confirm_deposit': '${amount} Onayla',
        'withdraw_submitted': 'Çekim isteği gönderildi! Admin bekleniyor...',
        'referral_text': """Referans Linkiniz:
`{ref_link}`

Referanslar: {ref_count}
%10 L1, %8 L2, %3 L3 komisyon!""",
        'support': 'Destek mesajınızı gönderin:',
        'choose_language': 'Dil seçin:',
        'english': 'English',
        'persian': 'فارسی',
        'turkish': 'Türkçe',
        'arabic': 'العربية',
        'daily_profit': 'Günlük kar eklendi: ${profit:.2f} (%{rate} oran)!\nYeni bakiye: ${new_balance:.2f}'
    },
    'ar': {
        'welcome': """مرحبا بك في Elite Yield Bot! 🚀

افتح عوائد يومية تصل إلى 21.7% على استثمارات USDT الخاصة بك! 💰

مستويات بناءً على الإيداع:
• $10-99: 16.6%
• $100-799: 17.9%  
• $800-2399: 19.6%
• $2400-5999: 21.7%

الحد الأدنى للإيداع: $10 USDT
الشبكات: TRC20 أو BEP20

ابدأ في كسب الدخل السلبي اليوم! 📈""",
        'balance_btn': 'الرصيد',
        'deposit_btn': 'إيداع',
        'withdraw_btn': 'سحب',
        'referral_btn': 'إحالة',
        'support_btn': 'دعم',
        'admin_btn': 'لوحة الإدارة',
        'support_tickets_btn': 'تذاكر الدعم',
        'balance': """رصيدك: ${balance:.2f} USDT
الربح الإجمالي: ${total_profit:.2f} USDT
المستوى: {level}""",
        'deposit_instructions': """تعليمات الإيداع:

أرسل USDT إلى:
TRC20: `{TRC20_WALLET}`
BEP20: `{BEP20_WALLET}`

الحد الأدنى $10. اضغط تأكيد بعد الإرسال.""",
        'enter_amount': 'أدخل المبلغ (حد أدنى $10):',
        'invalid_amount': 'غير صالح!',
        'confirm_deposit': 'تأكيد ${amount}',
        'withdraw_submitted': 'تم إرسال طلب السحب! انتظر الإدارة...',
        'referral_text': """رابط الإحالة الخاص بك:
`{ref_link}`

الإحالات: {ref_count}
10% L1, 8% L2, 3% L3 عمولة!""",
        'support': 'أرسل رسالتك إلى الدعم:',
        'choose_language': 'اختر اللغة:',
        'english': 'English',
        'persian': 'فارسی',
        'turkish': 'Türكçe',
        'arabic': 'العربية',
        'daily_profit': 'تم إضافة الربح اليومي: ${profit:.2f} (نسبة {rate}%)!\nالرصيد الجديد: ${new_balance:.2f}'
    }
}

def get_profit_rate(amount):
    if 2400 <= amount <= 5999:
        return 0.217
    if 800 <= amount <= 2399:
        return 0.196
    if 100 <= amount <= 799:
        return 0.179
    if 10 <= amount <= 99:
        return 0.166
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
    cursor = get_cursor()
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
    user_id = message.from_user.id
    username = message.from_user.username or f"User_{user_id}"
    args = message.text.split()
    
    referrer_id = None
    if len(args) > 1 and args[1].startswith('ref_'):
        try:
            referrer_id = int(args[1].split('_')[1])
            # avoid self-referral
            if referrer_id == user_id:
                referrer_id = None
        except Exception as e:
            logging.error(f'Referral parse error: {e}')
            referrer_id = None
    
    lang = get_user_lang(user_id)
    l = languages[lang]
    
    cursor = get_cursor()
    try:
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        if not cursor.fetchone():
            current_time = int(time.time())
            # insert user and set referrer if present
            cursor.execute('INSERT INTO users (user_id, username, created_at, language, referrer_id) VALUES (?, ?, ?, ?, ?)',
                           (user_id, username, current_time, lang, referrer_id))
            conn.commit()
            bot.send_message(message.chat.id, l['choose_language'], reply_markup=language_menu())
            # notify referrer if exists
            if referrer_id:
                try:
                    bot.send_message(referrer_id, 'New referral joined! You\'ll earn commissions from 3 levels!')
                except Exception as e:
                    logging.error(f'Notify referrer failed: {e}')
            return
    except Exception as e:
        logging.error(f'Start DB error: {e}')
    
    cursor.execute('UPDATE users SET username = ? WHERE user_id = ?', (username, user_id))
    conn.commit()
    
    is_admin = user_id == ADMIN_ID
    
    try:
        with open('welcome_banner.jpg', 'rb') as banner:
            bot.send_photo(message.chat.id, banner, caption=l['welcome'], reply_markup=main_menu(is_admin, lang))
    except FileNotFoundError:
        bot.send_message(message.chat.id, l['welcome'], reply_markup=main_menu(is_admin, lang))

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    cursor = get_cursor()
    lang = call.data.split('_')[1]
    try:
        cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (lang, call.from_user.id))
        conn.commit()
    except Exception as e:
        logging.error(f'Language update error: {e}')
    bot.answer_callback_query(call.id, "Language set!")
    # re-run start to show main menu in new language
    start_message(call.message)

# temporary storage for multi-step withdraw
withdraw_temp = {}

@bot.message_handler(func=lambda message: True)
def
