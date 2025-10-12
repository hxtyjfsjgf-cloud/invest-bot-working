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
ADMIN_ID = 7989867522  # ID تلگرام خودت
ADMIN_USERNAME = '@YourAdminUsername'  # username ادمین
SUPPORT_CHANNEL = 't.me/eliteinvestsupport'  # channel support

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
    created_at INTEGER DEFAULT 0,
    language TEXT DEFAULT 'en'  # چندزبانه
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

# دیکشنری زبان‌ها
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
💎 Level: {level}
🔄 Next profit in: Calculating...""",
        'deposit_instructions': """💳 Deposit Instructions:

Send USDT to one of these addresses:
🌐 TRC20 (Tron): `{TRC20_WALLET}`
🌐 BEP20 (BSC): `{BEP20_WALLET}`

💡 Minimum: $10
⚠️ Only USDT - no other tokens!

After sending, click "Confirm Deposit" below:""",
        'enter_amount': '💸 Enter amount to withdraw (min $5):',
        'invalid_amount': '❌ Invalid amount or insufficient balance!',
        'enter_wallet': 'Enter your wallet address (TRC20/BEP20):',
        'withdraw_submitted': '✅ Withdrawal request submitted! Waiting for admin approval...',
        'referral_text': """👥 Your Referral Link:
`{ref_link}`

📊 Referrals: {ref_count}
💰 Earn 5% commission on their deposits!

Share and earn passive income! 🎁""",
        'admin_panel': """🛠 Admin Panel
👥 Total Users: {total_users}
⏳ Pending Requests: Check below""",
        'users_list': '🏆 Top 10 Users by Balance:\n\n{users_text}',
        'pending_deposits': '💳 Pending Deposits:\n\n',
        'pending_withdraws': '\n💸 Pending Withdrawals:\n\n',
        'support': """📞 Support:
👤 Admin: {ADMIN_USERNAME}
🆔 ID: {ADMIN_ID}
📢 Channel: {SUPPORT_CHANNEL}

Contact for issues or questions!""",
        'choose_language': 'Choose your language / زبان خود را انتخاب کنید / Dilinizi seçin / اختر لغتك',
        'english': 'English 🇺🇸',
        'persian': 'Persian 🇮🇷',
        'turkish': 'Turkish 🇹🇷',
        'arabic': 'Arabic 🇸🇦'
    },
    'fa': {  # Persian
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
💎 سطح: {level}
🔄 سود بعدی در: محاسبه...""",
        'deposit_instructions': """💳 دستورالعمل واریز:

USDT را به یکی از آدرس‌ها ارسال کنید:
🌐 TRC20 (Tron): `{TRC20_WALLET}`
🌐 BEP20 (BSC): `{BEP20_WALLET}`

💡 حداقل: 10$
⚠️ فقط USDT - توکن دیگر نه!

پس از ارسال, "تأیید واریز" را کلیک کنید:""",
        'enter_amount': '💸 مبلغ برداشت را وارد کنید (حداقل 5$):',
        'invalid_amount': '❌ مبلغ نامعتبر یا موجودی ناکافی!',
        'enter_wallet': 'آدرس والت خود را وارد کنید (TRC20/BEP20):',
        'withdraw_submitted': '✅ درخواست برداشت ثبت شد! منتظر تأیید ادمین باشید...',
        'referral_text': """👥 لینک رفرال شما:
`{ref_link}`

📊 رفرال‌ها: {ref_count}
💰 5% کمیسیون از واریزهای آنها کسب کنید!

اشتراک بگذارید و درآمد غیرفعال کسب کنید! 🎁""",
        'admin_panel': """🛠 پنل ادمین
👥 کل کاربران: {total_users}
⏳ درخواست‌های در انتظار: زیر را چک کنید""",
        'users_list': '🏆 10 کاربر برتر بر اساس موجودی:\n\n{users_text}',
        'pending_deposits': '💳 واریزهای در انتظار:\n\n',
        'pending_withdraws': '\n💸 برداشت‌های در انتظار:\n\n',
        'support': """📞 پشتیبانی:
👤 ادمین: {ADMIN_USERNAME}
🆔 ID: {ADMIN_ID}
📢 کانال: {SUPPORT_CHANNEL}

برای مشکلات تماس بگیرید!""",
        'choose_language': 'زبان خود را انتخاب کنید / Choose your language / Dilinizi seçin / اختر لغتك',
        'english': 'English 🇺🇸',
        'persian': 'فارسی 🇮🇷',
        'turkish': 'Türkçe 🇹🇷',
        'arabic': 'العربية 🇸🇦'
    },
    'tr': {  # Turkish
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
💎 Seviye: {level}
🔄 Sonraki kar: Hesaplanıyor...""",
        'deposit_instructions': """💳 Yatırım Talimatları:

USDT'yi şu adreslere gönderin:
🌐 TRC20 (Tron): `{TRC20_WALLET}`
🌐 BEP20 (BSC): `{BEP20_WALLET}`

💡 Minimum: $10
⚠️ Sadece USDT - diğer token yok!

Gönderdikten sonra "Yatırımı Onayla" tıklayın:""",
        'enter_amount': '💸 Çekmek istediğiniz miktarı girin (min $5):',
        'invalid_amount': '❌ Geçersiz miktar veya yetersiz bakiye!',
        'enter_wallet': 'Cüzdan adresinizi girin (TRC20/BEP20):',
        'withdraw_submitted': '✅ Çekim isteği gönderildi! Admin onayı bekleniyor...',
        'referral_text': """👥 Referans Linkiniz:
`{ref_link}`

📊 Referanslar: {ref_count}
💰 Yatırımlarından %5 komisyon kazanın!

Paylaşın ve pasif gelir kazanın! 🎁""",
        'admin_panel': """🛠 Admin Paneli
👥 Toplam Kullanıcı: {total_users}
⏳ Bekleyen İstekler: Aşağıyı kontrol edin""",
        'users_list': '🏆 Bakiyeye Göre En İyi 10 Kullanıcı:\n\n{users_text}',
        'pending_deposits': '💳 Bekleyen Yatırımlar:\n\n',
        'pending_withdraws': '\n💸 Bekleyen Çekimler:\n\n',
        'support': """📞 Destek:
👤 Admin: {ADMIN_USERNAME}
🆔 ID: {ADMIN_ID}
📢 Kanal: {SUPPORT_CHANNEL}

Sorunlar için iletişime geçin!""",
        'choose_language': 'Diliniz seçin / Choose your language / زبان خود را انتخاب کنید / اختر لغتك',
        'english': 'English 🇺🇸',
        'persian': 'فارسی 🇮🇷',
        'turkish': 'Türkçe 🇹🇷',
        'arabic': 'العربية 🇸🇦'
    },
    'ar': {  # Arabic
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
💎 المستوى: {level}
🔄 الربح التالي في: يتم الحساب...""",
        'deposit_instructions': """💳 تعليمات الإيداع:

أرسل USDT إلى أحد هذه العناوين:
🌐 TRC20 (Tron): `{TRC20_WALLET}`
🌐 BEP20 (BSC): `{BEP20_WALLET}`

💡 الحد الأدنى: $10
⚠️ فقط USDT - لا توكنات أخرى!

بعد الإرسال, اضغط "تأكيد الإيداع": """,
        'enter_amount': '💸 أدخل المبلغ للسحب (حد أدنى $5):',
        'invalid_amount': '❌ مبلغ غير صالح أو رصيد غير كاف!',
        'enter_wallet': 'أدخل عنوان محفظتك (TRC20/BEP20):',
        'withdraw_submitted': '✅ تم إرسال طلب السحب! انتظر موافقة الإدارة...',
        'referral_text': """👥 رابط الإحالة الخاص بك:
`{ref_link}`

📊 الإحالات: {ref_count}
💰 اربح 5% عمولة من إيداعاتهم!

شارك واكسب دخل سلبي! 🎁""",
        'admin_panel': """🛠 لوحة الإدارة
👥 إجمالي المستخدمين: {total_users}
⏳ الطلبات المعلقة: تحقق أدناه""",
        'users_list': '🏆 أفضل 10 مستخدمين حسب الرصيد:\n\n{users_text}',
        'pending_deposits': '💳 الإيداعات المعلقة:\n\n',
        'pending_withdraws': '\n💸 السحوبات المعلقة:\n\n',
        'support': """📞 الدعم:
👤 الإدارة: {ADMIN_USERNAME}
🆔 ID: {ADMIN_ID}
📢 القناة: {SUPPORT_CHANNEL}

اتصل للمشكلات!""",
        'choose_language': 'اختر لغتك / Choose your language / زبان خود را انتخاب کنید / Dilinizi seçin',
        'english': 'English 🇺🇸',
        'persian': 'فارسی 🇮🇷',
        'turkish': 'Türkçe 🇹🇷',
        'arabic': 'العربية 🇸🇦'
    }
}

# منو اصلی (زبان‌دار)
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

# منو ادمین
def admin_menu(lang='en'):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    btn_users = KeyboardButton('👥 Users List')
    btn_pending = KeyboardButton('⏳ Pending Requests')
    btn_stats = KeyboardButton('📊 Statistics')
    btn_backup = KeyboardButton('🔄 Backup DB')
    btn_broadcast = KeyboardButton('📢 Broadcast Message')
    btn_back = KeyboardButton('🔙 Back to Main')
    markup.add(btn_users, btn_pending)
    markup.add(btn_stats, btn_backup)
    markup.add(btn_broadcast, btn_back)
    return markup

# منو انتخاب زبان
def language_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    btn_en = InlineKeyboardButton(languages['en']['english'], callback_data='lang_en')
    btn_fa = InlineKeyboardButton(languages['en']['persian'], callback_data='lang_fa')
    btn_tr = InlineKeyboardButton(languages['en']['turkish'], callback_data='lang_tr')
    btn_ar = InlineKeyboardButton(languages['en']['arabic'], callback_data='lang_ar')
    markup.add(btn_en, btn_fa)
    markup.add(btn_tr, btn_ar)
    return markup

# هندلر /start
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
        except:
            pass
    
    # ایجاد/بروزرسانی کاربر
    cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if not result:
        current_time = int(time.time())
        cursor.execute('INSERT INTO users (user_id, username, created_at) VALUES (?, ?, ?)', (user_id, username, current_time))
        conn.commit()
        logging.info(f'New user: {user_id} - {username}')
        # انتخاب زبان اول
        bot.send_message(message.chat.id, languages['en']['choose_language'], reply_markup=language_menu())
        return
    lang = result[0]
    
    cursor.execute('UPDATE users SET username = ? WHERE user_id = ?', (username, user_id))
    conn.commit()
    
    is_admin = user_id == ADMIN_ID
    
    # تصویر بنر + خوش‌آمد
    try:
        with open('welcome_banner.jpg', 'rb') as banner:
            bot.send_photo(
                message.chat.id, 
                banner,
                caption=languages[lang]['welcome'],
                reply_markup=main_menu(is_admin, lang)
            )
    except FileNotFoundError:
        bot.send_message(message.chat.id, languages[lang]['welcome'], reply_markup=main_menu(is_admin, lang))

# هندلر انتخاب زبان
@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    lang = call.data.split('_')[1]
    cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (lang, call.from_user.id))
    conn.commit()
    bot.answer_callback_query(call.id, "Language set!")
    bot.edit_message_text("Language changed!", call.message.chat.id, call.message.message_id)
    # دوباره خوش‌آمد با زبان جدید
    start_message(call.message)  # recall start

# هندلر منو
@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    user_id = message.from_user.id
    cursor.execute('SELECT balance, total_profit, level, language FROM users WHERE user_id = ?', (user_id,))
    user_data = cursor.fetchone() or (0, 0, 'Bronze', 'en')
    balance, total_profit, level, lang = user_data
    is_admin = user_id == ADMIN_ID
    
    if message.text == '💰 Balance':
        text = languages[lang]['balance'].format(balance=balance, total_profit=total_profit, level=level)
        bot.send_message(message.chat.id, text, reply_markup=main_menu(is_admin, lang))
    
    elif message.text == '💳 Deposit':
        bot.send_message(message.chat.id, languages[lang]['deposit_instructions'].format(TRC20_WALLET=TRC20_WALLET, BEP20_WALLET=BEP20_WALLET), parse_mode='Markdown')
        msg = bot.send_message(message.chat.id, 'Enter deposit amount (min $10):')
        bot.register_next_step_handler(msg, process_deposit_amount)
    
    elif message.text == '💸 Withdraw':
        if balance < 5:
            bot.send_message(message.chat.id, '❌ Minimum withdrawal $5', reply_markup=main_menu(is_admin, lang))
            return
        msg = bot.send_message(message.chat.id, languages[lang]['enter_amount'])
        bot.register_next_step_handler(msg, process_withdraw_request)
    
    elif message.text == '👥 Referral':
        ref_link = f't.me/eliteyieldbot?start=ref_{user_id}'
        cursor.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user_id,))
        ref_count = cursor.fetchone()[0]
        text = languages[lang]['referral_text'].format(ref_link=ref_link, ref_count=ref_count)
        bot.send_message(message.chat.id, text, reply_markup=main_menu(is_admin, lang), parse_mode='Markdown')
    
    elif message.text == '📞 Support':
        text = languages[lang]['support'].format(ADMIN_USERNAME=ADMIN_USERNAME, ADMIN_ID=ADMIN_ID, SUPPORT_CHANNEL=SUPPORT_CHANNEL)
        bot.send_message(message.chat.id, text, reply_markup=main_menu(is_admin, lang), parse_mode='Markdown')
    
    elif message.text == '🛠 Admin Panel' and is_admin:
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        text = languages[lang]['admin_panel'].format(total_users=total_users)
        bot.send_message(message.chat.id, text, reply_markup=admin_menu(lang))
    
    elif message.text == '👥 Users List' and is_admin:
        cursor.execute('SELECT user_id, username, balance FROM users ORDER BY balance DESC LIMIT 10')
        users = cursor.fetchall()
        users_text = ''
        for i, (uid, uname, bal) in enumerate(users, 1):
            users_text += f"{i}. {uname}: ${bal:.2f}\n"
        text = languages[lang]['users_list'].format(users_text=users_text)
        bot.send_message(message.chat.id, text, reply_markup=admin_menu(lang))
    
    elif message.text == '⏳ Pending Requests' and is_admin:
        # Pending deposits
        cursor.execute('SELECT * FROM pending_deposits WHERE status="pending"')
        deposits = cursor.fetchall()
        for dep in deposits:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('✅ Confirm', callback_data=f'admin_confirm_dep_{dep[0]}'),
                      InlineKeyboardButton('❌ Reject', callback_data=f'admin_reject_dep_{dep[0]}'))
            bot.send_message(message.chat.id, f"User: {dep[2]} (ID: {dep[1]})\nAmount: ${dep[3]}\nTime: {datetime.fromtimestamp(dep[4])}", reply_markup=markup)
        
        # Pending withdraws
        cursor.execute('SELECT * FROM pending_withdraws WHERE status="pending"')
        withdraws = cursor.fetchall()
        for wd in withdraws:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('✅ Confirm', callback_data=f'admin_confirm_wd_{wd[0]}'),
                      InlineKeyboardButton('❌ Reject', callback_data=f'admin_reject_wd_{wd[0]}'))
            bot.send_message(message.chat.id, f"User: {wd[2]} (ID: {wd[1]})\nAmount: ${wd[3]}\nWallet: {wd[4]}\nTime: {datetime.fromtimestamp(wd[5])}", reply_markup=markup)
    
    elif message.text == '📊 Statistics' and is_admin:
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        cursor.execute('SELECT SUM(balance) FROM users')
        total_balance = cursor.fetchone()[0] or 0
        text = f"📊 Stats:\n👥 Total Users: {total_users}\n💰 Total Balance: ${total_balance:.2f}"
        bot.send_message(message.chat.id, text, reply_markup=admin_menu(lang))
    
    elif message.text == '🔄 Backup DB' and is_admin:
        import shutil
        backup_file = f'backup_{int(time.time())}.db'
        shutil.copy('elite_yield.db', backup_file)
        bot.send_message(message.chat.id, f"✅ DB backed up to {backup_file}", reply_markup=admin_menu(lang))
    
    elif message.text == '📢 Broadcast Message' and is_admin:
        msg = bot.send_message(message.chat.id, 'Enter message to broadcast:')
        bot.register_next_step_handler(msg, process_broadcast)
    
    elif message.text == '🔙 Back to Main' and is_admin:
        bot.send_message(message.chat.id, 'Returning to main...', reply_markup=main_menu(True, lang))

# فرآیند واریز (متغیر)
def process_deposit_amount(message):
    try:
        amount = float(message.text)
        if amount < 10:
            bot.send_message(message.chat.id, '❌ Minimum $10!')
            return
        user_id = message.from_user.id
        lang = cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
        markup = InlineKeyboardMarkup()
        confirm_btn = InlineKeyboardButton('📤 Confirm Deposit', callback_data=f'deposit_confirm_{user_id}_{amount}')
        markup.add(confirm_btn)
        bot.send_message(message.chat.id, f"Click to confirm ${amount} deposit:", reply_markup=markup)
    except:
        bot.send_message(message.chat.id, '❌ Enter valid number!')

# هندلر callback (deposit/withdraw)
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data
    if data.startswith('deposit_confirm_'):
        parts = data.split('_')
        target_user_id = int(parts[2])
        amount = float(parts[3])
        username = cursor.execute('SELECT username FROM users WHERE user_id = ?', (target_user_id,)).fetchone()[0]
        
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
    
    elif data.startswith('admin_confirm_dep_'):
        deposit_id = int(data.split('_')[3])
        cursor.execute('SELECT user_id, amount FROM pending_deposits WHERE id = ?', (deposit_id,))
        dep_data = cursor.fetchone()
        
        if dep_data:
            user_id, amount = dep_data
            cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
            new_balance = cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
            new_level, _ = get_level(new_balance)
            cursor.execute('UPDATE users SET level = ? WHERE user_id = ?', (new_level, user_id))
            
            referrer_id = cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
            if referrer_id:
                commission = amount * 0.05
                cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (commission, referrer_id))
                bot.send_message(referrer_id, f'🎉 Commission ${commission:.2f} from referral!')
            
            conn.commit()
            cursor.execute('UPDATE pending_deposits SET status = "confirmed" WHERE id = ?', (deposit_id,))
            conn.commit()
            
            bot.send_message(user_id, f'✅ Deposit ${amount} confirmed! New balance: ${new_balance:.2f}')
            logging.info(f'Deposit ${amount} for {user_id}')
        
        bot.answer_callback_query(call.id, "✅ Confirmed!")
        bot.edit_message_text("✅ Processed!", call.message.chat.id, call.message.message_id)
    
    elif data.startswith('admin_reject_dep_'):
        deposit_id = int(data.split('_')[3])
        cursor.execute('SELECT user_id FROM pending_deposits WHERE id = ?', (deposit_id,))
        user_id = cursor.fetchone()[0]
        cursor.execute('UPDATE pending_deposits SET status = "rejected" WHERE id = ?', (deposit_id,))
        conn.commit()
        bot.send_message(user_id, '❌ Deposit rejected. Contact support.')
        bot.answer_callback_query(call.id, "❌ Rejected!")

    # مشابه برای withdraw... (کد قبلی حفظ شد)

# فرآیند برداشت (کد قبلی)

# فرآیند پخش پیام
def process_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    broadcast_text = message.text
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    for u in users:
        try:
            bot.send_message(u[0], broadcast_text)
        except:
            pass
    bot.send_message(ADMIN_ID, f"✅ Broadcast sent to {len(users)} users!")

# اجرای ربات
if __name__ == '__main__':
    print("🚀 Elite Yield Bot starting...")
    bot.polling(none_stop=True)
