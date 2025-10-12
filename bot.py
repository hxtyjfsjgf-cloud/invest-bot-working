import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import threading
import time
import logging
from datetime import datetime

# تنظیم لاگینگ
logging.basicConfig(filename='bot_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

# توکن و تنظیمات
BOT_TOKEN = '8268425583:AAFkSCeYzXAU2gcyz-tZLSwpzVg0uZ061IU'  # توکن از BotFather
ADMIN_ID = 7989867522  # ID تلگرام خودت (از @userinfobot بگیر)

# آدرس والت‌های ثابت
TRC20_WALLET = "TQzZgrHNtG9i8mGufpvW12sxFuy"  # والت TRC20 واقعی خودت
BEP20_WALLET = "0x7485e33695b722aA071A868bb6959533a3e449b02E"  # والت BEP20 واقعی خودت

bot = telebot.TeleBot(BOT_TOKEN)

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
    created_at INTEGER DEFAULT 0
)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS pending_deposits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    amount REAL DEFAULT 10,
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

def get_level(balance):
    if balance < 100:
        return 'Bronze', 0.10
    elif balance < 500:
        return 'Silver', 0.12
    else:
        return 'Gold', 0.16

def main_menu(is_admin=False):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_balance = KeyboardButton('💰 Balance')
    btn_deposit = KeyboardButton('💳 Deposit')
    btn_withdraw = KeyboardButton('💸 Withdraw')
    btn_referral = KeyboardButton('👥 Referral')
    markup.add(btn_balance, btn_deposit)
    markup.add(btn_withdraw, btn_referral)
    
    if is_admin:
        btn_admin = KeyboardButton('🛠 Admin Panel')
        markup.add(btn_admin)
    return markup

def admin_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    btn_users = KeyboardButton('👥 Users List')
    btn_pending = KeyboardButton('⏳ Pending Requests')
    btn_stats = KeyboardButton('📊 Statistics')
    btn_back = KeyboardButton('🔙 Back to Main')
    markup.add(btn_users, btn_pending)
    markup.add(btn_stats, btn_back)
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
            if referrer_id != user_id:  # خودreferral نباشه
                cursor.execute('UPDATE users SET referrer_id = ? WHERE user_id = ?', (referrer_id, user_id))
                conn.commit()
                bot.send_message(referrer_id, '🎉 New referral joined! You\'ll earn 5% commission on their deposits!')
        except:
            pass
    
    # ایجاد کاربر جدید
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    if not cursor.fetchone():
        current_time = int(time.time())
        cursor.execute('INSERT INTO users (user_id, username, created_at) VALUES (?, ?, ?)', 
                      (user_id, username, current_time))
        conn.commit()
        logging.info(f'New user registered: {user_id} - {username}')
    
    # بروزرسانی username
    cursor.execute('UPDATE users SET username = ? WHERE user_id = ?', (username, user_id))
    conn.commit()
    
    is_admin = user_id == ADMIN_ID
    welcome_text = """🌟 Welcome to Elite Yield Bot! 🚀

Unlock up to 16% DAILY returns on your USDT investments! 💰

💎 Membership Levels:
• Bronze (10% daily) - $0-$99
• Silver (12% daily) - $100-$499  
• Gold (16% daily) - $500+

💳 Minimum deposit: $10 USDT
🌐 Networks: TRC20 or BEP20

Start earning passive income today! 📈"""
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu(is_admin))

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    user_id = message.from_user.id
    is_admin = user_id == ADMIN_ID
    
    cursor.execute('SELECT balance, total_profit, level FROM users WHERE user_id = ?', (user_id,))
    user_data = cursor.fetchone() or (0, 0, 'Bronze')
    balance, total_profit, level = user_data
    
    if message.text == '💰 Balance':
        text = f"""💰 Your Balance: ${balance:.2f} USDT
📈 Total Profit: ${total_profit:.2f} USDT
💎 Level: {level}
🔄 Next profit in: Calculating..."""
        bot.send_message(message.chat.id, text, reply_markup=main_menu(is_admin))
    
    elif message.text == '💳 Deposit':
        deposit_text = f"""💳 Deposit Instructions:

Send USDT to one of these addresses:
🌐 TRC20 (Tron): `{TRC20_WALLET}`
🌐 BEP20 (BSC): `{BEP20_WALLET}`

💡 Minimum: $10
⚠️ Only USDT - no other tokens!

After sending, click "Confirm Deposit" below:"""
        
        markup = InlineKeyboardMarkup()
        confirm_btn = InlineKeyboardButton('📤 Confirm Deposit', callback_data=f'deposit_confirm_{user_id}')
        markup.add(confirm_btn)
        
        bot.send_message(message.chat.id, deposit_text, reply_markup=main_menu(is_admin), parse_mode='Markdown')
        bot.send_message(message.chat.id, "Click to confirm your deposit:", reply_markup=markup)
    
    elif message.text == '💸 Withdraw':
        if balance < 5:
            bot.send_message(message.chat.id, '❌ Minimum withdrawal: $5', reply_markup=main_menu(is_admin))
            return
        msg = bot.send_message(message.chat.id, '💸 Enter amount to withdraw (min $5):')
        bot.register_next_step_handler(msg, process_withdraw_request)
    
    elif message.text == '👥 Referral':
        ref_link = f't.me/eliteyieldbot?start=ref_{user_id}'  # username ربات رو عوض کن
        cursor.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user_id,))
        ref_count = cursor.fetchone()[0]
        text = f"""👥 Your Referral Link:
`{ref_link}`

📊 Referrals: {ref_count}
💰 Earn 5% commission on their deposits!

Share and earn passive income! 🎁"""
        bot.send_message(message.chat.id, text, reply_markup=main_menu(is_admin), parse_mode='Markdown')
    
    elif message.text == '🛠 Admin Panel' and is_admin:
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        text = f"""🛠 Admin Panel
👥 Total Users: {total_users}
⏳ Pending Requests: Check below"""
        bot.send_message(message.chat.id, text, reply_markup=admin_menu())
    
    elif message.text == '👥 Users List' and is_admin:
        cursor.execute('SELECT user_id, username, balance FROM users ORDER BY balance DESC LIMIT 10')
        users = cursor.fetchall()
        text = '🏆 Top 10 Users by Balance:\n\n'
        for i, (uid, uname, bal) in enumerate(users, 1):
            text += f"{i}. {uname}: ${bal:.2f}\n"
        bot.send_message(message.chat.id, text, reply_markup=admin_menu())
    
    elif message.text == '⏳ Pending Requests' and is_admin:
        # Pending deposits
        cursor.execute('SELECT * FROM pending_deposits WHERE status="pending"')
        deposits = cursor.fetchall()
        text = '💳 Pending Deposits:\n\n'
        for dep in deposits:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('✅ Confirm', callback_data=f'admin_confirm_dep_{dep[0]}'),
                      InlineKeyboardButton('❌ Reject', callback_data=f'admin_reject_dep_{dep[0]}'))
            bot.send_message(message.chat.id, f"User: {dep[2]} (ID: {dep[1]})\nAmount: ${dep[3]}\nTime: {datetime.fromtimestamp(dep[4])}", reply_markup=markup)
        
        # Pending withdraws
        cursor.execute('SELECT * FROM pending_withdraws WHERE status="pending"')
        withdraws = cursor.fetchall()
        text = '\n💸 Pending Withdrawals:\n\n'
        for wd in withdraws:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('✅ Confirm', callback_data=f'admin_confirm_wd_{wd[0]}'),
                      InlineKeyboardButton('❌ Reject', callback_data=f'admin_reject_wd_{wd[0]}'))
            bot.send_message(message.chat.id, f"User: {wd[2]} (ID: {wd[1]})\nAmount: ${wd[3]}\nWallet: {wd[4]}\nTime: {datetime.fromtimestamp(wd[5])}", reply_markup=markup)
    
    elif message.text == '🔙 Back to Main' and is_admin:
        bot.send_message(message.chat.id, 'Returning to main menu...', reply_markup=main_menu(True))

def process_withdraw_request(message):
    try:
        amount = float(message.text)
        user_id = message.from_user.id
        cursor.execute('SELECT balance, username FROM users WHERE user_id = ?', (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data or amount > user_data[0] or amount < 5:
            bot.send_message(message.chat.id, '❌ Invalid amount or insufficient balance!', reply_markup=main_menu(user_id == ADMIN_ID))
            return
        
        username = user_data[1]
        wallet_msg = bot.send_message(message.chat.id, 'Enter your wallet address (TRC20/BEP20):')
        bot.register_next_step_handler(wallet_msg, lambda msg: process_withdraw_wallet(msg, amount, username))
    except:
        bot.send_message(message.chat.id, '❌ Enter valid number!', reply_markup=main_menu(user_id == ADMIN_ID))

def process_withdraw_wallet(message, amount, username):
    wallet_address = message.text
    user_id = message.from_user.id
    
    # ذخیره درخواست برداشت
    current_time = int(time.time())
    cursor.execute('INSERT INTO pending_withdraws (user_id, username, amount, wallet_address, created_at) VALUES (?, ?, ?, ?, ?)',
                  (user_id, username, amount, wallet_address, current_time))
    conn.commit()
    
    # اطلاع به ادمین
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('✅ Confirm', callback_data=f'admin_confirm_wd_{cursor.lastrowid}'),
              InlineKeyboardButton('❌ Reject', callback_data=f'admin_reject_wd_{cursor.lastrowid}'))
    
    admin_msg = f"💸 New Withdrawal Request:\nUser: {username} (ID: {user_id})\nAmount: ${amount}\nWallet: {wallet_address}"
    bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup)
    
    bot.send_message(message.chat.id, '✅ Withdrawal request submitted! Waiting for admin approval...', reply_markup=main_menu(user_id == ADMIN_ID))

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data
    user_id = call.from_user.id
    
    if data.startswith('deposit_confirm_'):
        target_user_id = int(data.split('_')[2])
        username = cursor.execute('SELECT username FROM users WHERE user_id = ?', (target_user_id,)).fetchone()[0]
        
        # ذخیره درخواست واریز
        current_time = int(time.time())
        cursor.execute('INSERT INTO pending_deposits (user_id, username, created_at) VALUES (?, ?, ?)',
                      (target_user_id, username, current_time))
        deposit_id = cursor.lastrowid
        conn.commit()
        
        # اطلاع به ادمین
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('✅ Confirm ($10)', callback_data=f'admin_confirm_dep_{deposit_id}'),
                  InlineKeyboardButton('❌ Reject', callback_data=f'admin_reject_dep_{deposit_id}'))
        
        admin_msg = f"💳 New Deposit Request:\nUser: {username} (ID: {target_user_id})\nAmount: $10 (default)"
        bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup)
        
        bot.answer_callback_query(call.id, "✅ Deposit request sent to admin!")
        bot.edit_message_text("✅ Your deposit request has been submitted! Admin will confirm soon.", call.message.chat.id, call.message.message_id)
    
    elif data.startswith('admin_confirm_dep_'):
        deposit_id = int(data.split('_')[3])
        cursor.execute('SELECT user_id, amount FROM pending_deposits WHERE id = ?', (deposit_id,))
        dep_data = cursor.fetchone()
        
        if dep_data:
            user_id, amount = dep_data
            # اضافه کردن موجودی
            cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
            
            # بروزرسانی سطح
            new_balance = cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
            new_level, _ = get_level(new_balance)
            cursor.execute('UPDATE users SET level = ? WHERE user_id = ?', (new_level, user_id))
            
            # کمیسیون referral
            referrer_id = cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
            if referrer_id:
                commission = amount * 0.05
                cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (commission, referrer_id))
                bot.send_message(referrer_id, f'🎉 Referral commission: ${commission:.2f} added to your balance!')
            
            conn.commit()
            
            # بروزرسانی status
            cursor.execute('UPDATE pending_deposits SET status = "confirmed" WHERE id = ?', (deposit_id,))
            conn.commit()
            
            bot.send_message(user_id, f'✅ Deposit confirmed! ${amount} added to your balance!\nNew balance: ${new_balance:.2f}')
            logging.info(f'Deposit confirmed: ${amount} for user {user_id}')
        
        bot.answer_callback_query(call.id, "✅ Deposit confirmed!")
        bot.edit_message_text("✅ Deposit confirmed and processed!", call.message.chat.id, call.message.message_id)
    
    elif data.startswith('admin_reject_dep_'):
        deposit_id = int(data.split('_')[3])
        cursor.execute('SELECT user_id FROM pending_deposits WHERE id = ?', (deposit_id,))
        user_id = cursor.fetchone()[0]
        
        cursor.execute('UPDATE pending_deposits SET status = "rejected" WHERE id = ?', (deposit_id,))
        conn.commit()
        
        bot.send_message(user_id, '❌ Deposit request rejected. Please contact admin.')
        bot.answer_callback_query(call.id, "❌ Deposit rejected!")
    
    # مشابه برای withdraw...

# اجرای ربات
if __name__ == '__main__':
    print("🚀 Elite Yield Bot starting...")
    print("💡 Admin ID:", ADMIN_ID)
    print("📱 Bot is online! Press Ctrl+C to stop.")
    bot.polling(none_stop=True)
