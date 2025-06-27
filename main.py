import os
import requests
import openai
from binance.client import Client
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler
import logging

# الحصول على المفاتيح من متغيرات البيئة
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# إعداد
openai.api_key = OPENAI_API_KEY
binance_client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_price(symbol):
    try:
        ticker = binance_client.get_symbol_ticker(symbol=f"{symbol.upper()}USDT")
        return float(ticker['price'])
    except Exception as e:
        print(f"Binance API error: {e}")
        return None

def generate_ai_recommendation(symbol, price):
    prompt = f"""أنت محلل مالي محترف.
    أعطني توصية تداول مفصلة لعملة {symbol.upper()} بناءً على سعرها الحالي {price} USDT.
    يجب أن تحتوي على:
    - الاتجاه المتوقع (صعود أو هبوط)
    - سعر التقديم المناسب (entry price)
    - هدف أول وهدف ثاني
    - وقف الخسارة
    - نصيحة إدارة رأس المال
    اجعل النص واضحًا واحترافيًا."""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=400,
    )
    return response.choices[0].message["content"]

def start(update: Update, context):
    update.message.reply_text("👋 مرحبًا! أرسل لي /coin <رمز> مثل:\n/coin BTC\nلتحصل على توصية ذكية.")
def coin(update: Update, context):
    print(f"[DEBUG] Received /coin command with args: {context.args}")
    if len(context.args) == 0:
        update.message.reply_text("⚠️ اكتب الرمز هكذا:\n/coin BTC")
        return
    symbol = context.args[0].upper()
    price = get_price(symbol)
    print(f"[DEBUG] Fetched price for {symbol}: {price}")
    if price:
        recommendation = generate_ai_recommendation(symbol, price)
        print(f"[DEBUG] AI recommendation: {recommendation}")
        update.message.reply_text(f"💹 السعر الحالي لـ {symbol}: {price} USDT\n\n{recommendation}")
    else:
        update.message.reply_text("⚠️ تعذر جلب السعر من Binance. تحقق من الرمز أو حاول لاحقًا.")

def test(update: Update, context):
    update.message.reply_text("✅ البوت استلم أمر /test بنجاح.")

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("coin", coin))
    updater.start_polling()
    updater.idle()
dp.add_handler(CommandHandler("test", test))


if __name__ == '__main__':
    main()
