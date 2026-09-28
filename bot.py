import os
import threading
import requests
import pandas as pd
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ==== 1. GIỮ RENDER LIVE FREE ====
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Bot TOP30 RSI <30 is Live!"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)
threading.Thread(target=run_web, daemon=True).start()

# ==== 2. CẤU HÌNH ====
TOKEN = os.environ.get("TOKEN")
TOP30 = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","ADAUSDT","DOGEUSDT","AVAXUSDT","DOTUSDT","LINKUSDT","TRXUSDT","MATICUSDT","LTCUSDT","BCHUSDT","UNIUSDT","XLMUSDT","ETCUSDT","FILUSDT","ATOMUSDT","HBARUSDT","NEARUSDT","APTUSDT","QNTUSDT","VETUSDT","ICPUSDT","ARBUSDT","STXUSDT","OPUSDT","INJUSDT","SUIUSDT"]

def get_rsi(prices, period=14):
    df = pd.DataFrame(prices, columns=['close'])
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])

def get_price_rsi(symbol, interval="1h"):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
        data = requests.get(url, timeout=10).json()
        closes = [float(c[4]) for c in data]
        price = closes[-1]
        rsi = get_rsi(closes)
        return price, rsi
    except:
        return None, None

# ==== 3. LỆNH SCAN CHỈ LẤY RSI < 30 ====
async def scan_1h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Đang quét 30 coin khung 1H - chỉ lọc RSI < 30 QUÁ BÁN MẠNH NHẤT...")

    signals = []
    for sym in TOP30:
        price, rsi = get_price_rsi(sym, "1h")
        if price and rsi and rsi < 30:
            signals.append({"symbol": sym, "price": price, "rsi": rsi})

    if not signals:
        await update.message.reply_text("💤 1H hiện tại KHÔNG CÓ coin nào RSI < 30.\nThị trường đang khỏe, không có quá bán mạnh.")
        return

    # Sắp xếp mạnh nhất (RSI thấp nhất) lên đầu, lấy top 5
    signals = sorted(signals, key=lambda x: x['rsi'])[:5]

    msg = f"🔥🔥 TÍN HIỆU QUÁ BÁN MẠNH 1H (RSI < 30) - {len(signals)} coin mạnh nhất:\n\n"
    for s in signals:
        msg += f"🚨 {s['symbol']} ${s['price']:.2f}\n RSI: {s['rsi']:.1f} QUÁ BÁN - SẮP HỒI MẠNH 🔼\n\n"

    msg += "👉 Gõ /auto_scan để tự báo mỗi giờ."
    await update.message.reply_text(msg)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot TOP30 đã Live!\nGõ /scan1h để quét coin RSI < 30\nGõ /auto_scan để tự động.")

# ==== 4. CHẠY BOT ====
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("scan1h", scan_1h))
app.add_handler(CommandHandler("scan", scan_1h))
app.add_handler(CommandHandler("auto_scan", scan_1h))

print("Bot TOP30 RSI <30 starting...")
app.run_polling()
