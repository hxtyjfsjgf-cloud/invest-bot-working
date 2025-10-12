import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import threading
import time
import logging
from datetime import datetime

logging.basicConfig(filename='bot_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

BOT_TOKEN = 'YOUR_TOKEN'  # عوض کن
ADMIN_ID = 123456789
ADMIN_USERNAME = '@YourAdmin'

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

# زبان‌ها (منوها زبان‌دار شد, e.g. Balance -> languages[lang]['balance_btn'])
languages = {
    'en': {
        'welcome': 'Welcome! 🚀',
        'balance_btn': '💰 Balance',
        'deposit_btn': '💳 Deposit',
        'withdraw_btn': '💸 Withdraw',
        'referral_btn': '👥 Referral',
        'support_btn': '📞 Support',
        'admin_btn': '🛠 Admin Panel',
        'balance_text': 'Balance: ${balance}',
        'deposit_instructions': 'Send to TRC20: {trc} or BEP20: {bep}\nEnter amount (min $10):',
        'enter_amount': 'Enter amount:',
        'confirm_deposit': 'Confirm ${amount}',
        'support_text': 'Send your message to support:',
        'support_admin_new': 'New support message from {username} (ID: {user_id}): {text}',
        'referral_text': 'Referral link: {link}\nReferrals: {count}',
        'profit_rates': {10: 0.166, 100: 0.179, 800: 0.196, 2400: 0.217},
        'daily_profit': 'Daily profit added: ${profit} at {rate}%!'
    },
    # fa, tr, ar مشابه, btnها ترجمه (مثل 'موجودی' برای fa)
    'fa': {
        'welcome': 'خوش آمدید! 🚀',
        'balance_btn': '💰 موجودی',
        'deposit_btn': '💳 واریز',
        'withdraw_btn': '💸 برداشت',
        'referral_btn': '👥 رفرال',
        'support_btn': '📞 پشتیبانی',
        'admin_btn': '🛠 پنل ادمین',
        # ... بقیه ترجمه
    },
    # tr and ar similar
}

def get_profit_rate(amount):
    if 2400 <= amount <= 5999: return 0.217
    if 800 <= amount <= 2399: return 0.196
    if 100 <= amount <= 799: return 0.179
    if 10 <= amount <= 99: return 0.166
    return 0

def get_level(amount):
    if 2400 <= amount <= 5999: return 'Level4', 0.217
    if 800 <= amount <= 2399: return 'Level3', 0.196
    if 100 <= amount <= 799: return 'Level2', 0.179
    if 10 <= amount <= 99: return 'Level1', 0.166
    return 'None', 0

def main_menu(is_admin=False, lang='en'):
    l = languages[lang]
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(l['balance_btn'], l['deposit_btn'])
    markup.add(l['withdraw_btn'], l['referral_btn'])
    markup.add(l['support_btn'])
    if is_admin:
        markup.add(l['admin_btn'])
    return markup

@bot.message_handler(commands=['start'])
def start_message(message):
    # ... (زبان انتخاب, lang from db)
    lang = 'en'  # get from db
    l = languages[lang]
    try:
        with open('welcome_banner.jpg', 'rb') as banner:
            bot.send_photo(message.chat.id, banner, caption=l['welcome'], reply_markup=main_menu(is_admin, lang))
    except:
        bot.send_message(message.chat.id, l['welcome'], reply_markup=main_menu(is_admin, lang))

@bot.message_handler(func=lambda m: m.text == languages[m.language]['deposit_btn'])  # زبان‌دار
def deposit_handler(message):
    lang = get_user_lang(message.from_user.id)
    l = languages[lang]
    bot.send_message(message.chat.id, l['deposit_instructions'].format(trc=TRC20_WALLET, bep=BEP20_WALLET))
    msg = bot.send_message(message.chat.id, l['enter_amount'])
    bot.register_next_step_handler(msg, process_deposit_amount, lang)

def process_deposit_amount(message, lang):
    try:
        amount = float(message.text)
        if amount < 10:
            bot.send_message(message.chat.id, 'Min $10!')
            return
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(l['confirm_deposit'].format(amount=amount), callback_data=f'dep_confirm_{message.from_user.id}_{amount}'))
        bot.send_message(message.chat.id, 'Confirm?', reply_markup=markup)
    except:
        bot.send_message(message.chat.id, 'Invalid!')

# callback dep_confirm
@bot.callback_query_handler(func=lambda call: call.data.startswith('dep_confirm_'))
def dep_confirm(call):
    parts = call.data.split('_')
    user_id = int(parts[2])
    amount = float(parts[3])
    # pending_deposits insert
    cursor.execute('INSERT INTO pending_deposits (user_id, amount, created_at) VALUES (?, ?, ?)', (user_id, amount, int(time.time())))
    conn.commit()
    bot.send_message(ADMIN_ID, f'New deposit request: User {user_id} Amount ${amount} - Confirm?')
    bot.answer_callback_query(call.id, 'Submitted!')

# ساپورت پیشرفته
@bot.message_handler(func=lambda m: m.text == languages[get_user_lang(m.from_user.id)]['support_btn'])
def support_handler(message):
    lang = get_user_lang(message.from_user.id)
    bot.send_message(message.chat.id, languages[lang]['support_text'])
    bot.register_next_step_handler(message, forward_to_admin)

def forward_to_admin(message):
    user_id = message.from_user.id
    username = message.from_user.username or 'Unknown'
    text = message.text
    current_time = int(time.time())
    cursor.execute('INSERT INTO support_messages (user_id, username, message_text, created_at) VALUES (?, ?, ?, ?)', (user_id, username, text, current_time))
    conn.commit()
    msg_id = cursor.lastrowid
    forward_msg = bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Reply', callback_data=f'support_reply_{msg_id}'), InlineKeyboardButton('Seen', callback_data=f'support_seen_{msg_id}'))
    bot.send_message(ADMIN_ID, f"Support ticket {msg_id} from {username} (ID: {user_id})", reply_markup=markup)
    bot.send_message(message.chat.id, 'Message sent to support!')

@bot.callback_query_handler(func=lambda call: call.data.startswith('support_reply_'))
def support_reply(call):
    msg_id = call.data.split('_')[2]
    msg = bot.send_message(ADMIN_ID, 'Enter reply:')
    bot.register_next_step_handler(msg, lambda m: send_reply(m, msg_id))

def send_reply(message, msg_id):
    reply_text = message.text
    cursor.execute('SELECT user_id FROM support_messages WHERE id = ?', (msg_id,))
    user_id = cursor.fetchone()[0]
    conn.commit()
    bot.send_message(user_id, f"Support reply: {reply_text}")
    cursor.execute('UPDATE support_messages SET status = "replied" WHERE id = ?', (msg_id,))
    conn.commit()
    bot.send_message(ADMIN_ID, 'Reply sent!')

# پنل ادمین: Pending support
elif message.text == '📞 Support Tickets' and is_admin:
    cursor.execute('SELECT id, user_id, username, message_text, created_at FROM support_messages WHERE status = "new" ORDER BY created_at DESC')
    tickets = cursor.fetchall()
    conn.commit()
    for ticket in tickets:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('Reply', callback_data=f'support_reply_{ticket[0]}'), InlineKeyboardButton('Seen', callback_data=f'support_seen_{ticket[0]}'))
        bot.send_message(message.chat.id, f"Ticket {ticket[0]} from {ticket[2]} (ID: {ticket[1]})\nText: {ticket[3]}\nTime: {datetime.fromtimestamp(ticket[4])}", reply_markup=markup)

# رفرال سه سطحی
def calculate_referral_commission(deposit_amount, referrer_id):
    if not referrer_id:
        return
    level1_rate = 0.10
    level2_rate = 0.08
    level3_rate = 0.03
    
    # Level 1
    commission1 = deposit_amount * level1_rate
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (commission1, referrer_id))
    conn.commit()
    bot.send_message(referrer_id, f'Level 1 commission: ${commission1}')
    
    # Find level 2
    cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (referrer_id,))
    level2 = cursor.fetchone()
    if level2 and level2[0]:
        commission2 = deposit_amount * level2_rate
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (commission2, level2[0]))
        conn.commit()
        bot.send_message(level2[0], f'Level 2 commission: ${commission2}')
        
        # Level 3
        cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (level2[0],))
        level3 = cursor.fetchone()
        if level3 and level3[0]:
            commission3 = deposit_amount * level3_rate
            cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (commission3, level3[0]))
            conn.commit()
            bot.send_message(level3[0], f'Level 3 commission: ${commission3}')

# در admin_confirm_dep_
# بعد اضافه balance
referrer_id = cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
calculate_referral_commission(amount, referrer_id)

# سود دهی
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
                    bot.send_message(user_id, languages[lang]['daily_profit'].format(profit=profit, rate=rate*100))
        except Exception as e:
            logging.error(f'Profit error: {e}')
        time.sleep(3600)

threading.Thread(target=add_daily_profit, daemon=True).start()

# در confirm deposit
# deposit_amount = amount (برای سود بر اساس deposit)
cursor.execute('UPDATE users SET deposit_amount = ? WHERE user_id = ?', (amount, user_id))

# min withdraw $1
if balance < 1:
    # in withdraw

# commit کن و Render deploy.
