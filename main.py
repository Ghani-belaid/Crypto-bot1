import os
import requests
import openai
from binance.client import Client
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler
from flask import Flask, request
import logging

# إعداد المفاتيح
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# إعداد المكتبات
openai.api_key = OPENAI_API_KEY
binance_client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

# إعداد Flask
app = Flask(__name__)

# إعداد Dispatcher
dispatcher = Dispatcher(bot, None, workers=0)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# دوال الأوامر
def start(update: Update, context):
    update.message.reply_text("👋 مرحبًا بك! أرسل لي /coin BTC للحصول على توصية.")

def test(update: Update, context):
    print("[DEBUG] /test called")
    update.message.reply_text("✅ البوت استلم أمر /test بنجاح.")

def coin(update: Update, context):
    print(f"[DEBUG] /coin called with args: {context.args}")
    if len(context.args) == 0:
        update.message.reply_text("⚠️ اكتب هكذا: /coin BTC")
        return
    symbol = context.args[0].upper()
    price = get_price(symbol)
    print(f"[DEBUG] Fetched price for {symbol}: {price}")
    if price:
        recommendation = generate_ai_recommendation(symbol, price)
        print(f"[DEBUG] AI recommendation: {recommendation}")
        update.message.reply_text(f"💹 السعر الحالي لـ {symbol}: {price} USDT\n\n{recommendation}")
    else:
        update.message.reply_text("⚠️ تعذر جلب السعر من Binance. تأكد من الرمز.")

# تسجيل الأوامر
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("test", test))
dispatcher.add_handler(CommandHandler("coin", coin))

# دوال مساعدة
def get_price(symbol):
    try:
        ticker = binance_client.get_symbol_ticker(symbol=f"{symbol.upper()}USDT")
        return float(ticker['price'])
    except Exception as e:
        print(f"[Binance Error] {e}")
        return None

def generate_ai_recommendation(symbol, price):
    prompt = f"""أنت محلل مالي محترف.
    أعطني توصية تداول مفصلة لعملة {symbol.upper()} بناءً على سعرها الحالي {price} USDT.
    يجب أن تحتوي على:
    - الاتجاه المتوقع (صعود أو هبوط)
    - سعر التقديم المناسب
    - هدف أول وهدف ثاني
    - وقف الخسارة
    - نصيحة إدارة رأس المال
    كن محترفًا وواضحًا."""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=400,
    )
    return response.choices[0].message["content"]

# إعداد Webhook endpoint
@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

# تعيين الـ Webhook على Telegram
@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TELEGRAM_TOKEN}"
    success = bot.set_webhook(url=url)
    return f"Webhook setup: {success}"

# تشغيل التطبيق
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
