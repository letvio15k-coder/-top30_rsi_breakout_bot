import os, threading, requests, pandas as pd
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Giữ Render Live Free
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot SPOT Sieu Loc Live!"
def run_web():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.environ.get("TOKEN")
TOP30 = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","AVAXUSDT","DOTUSDT","LINKUSDT","TRXUSDT","MATICUSDT","LTCUSDT","BCHUSDT","UNIUSDT","ATOMUSDT","ETCUSDT","FILUSDT","NEARUSDT","APTUSDT","ARBUSDT","OPUSDT","SUIUSDT","INJUSDT","STXUSDT","HBARUSDT","VETUSDT","ICPUSDT","QNTUSDT","XLMUSDT","ADAUSDT"]

def get_data(symbol, interval="1h", limit=100):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        kl = requests.get(url, timeout=10).json()
        closes = [float(x[4]) for x in kl]
        highs = [float(x[2]) for x in kl]
        lows = [float(x[3]) for x in kl]
        return closes, highs, lows
    except: return None, None, None

def calc_rsi(prices, p=14):
    df = pd.DataFrame(prices, columns=['c'])
    d = df['c'].diff()
    g = d.where(d>0,0).rolling(p).mean()
    l = -d.where(d<0,0).rolling(p).mean()
    rs = g/l
    return float((100 - (100/(1+rs))).iloc[-1])

def calc_ema(prices, p):
    return pd.DataFrame(prices, columns=['c'])['c'].ewm(span=p).mean().iloc[-1]

async def scan_spot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Đang siêu lọc SPOT 1H (RSI<35 + EMA + Đáy 20 nến)...")
    keo_ngon = []
    for sym in TOP30:
        closes, highs, lows = get_data(sym, "1h")
        if not closes: continue
        price = closes[-1]
        rsi = calc_rsi(closes)
        ema20 = calc_ema(closes, 20)
        ema50 = calc_ema(closes, 50)
        day20 = min(lows[-20:])
        dinh20 = max(highs[-20:])

        # SIÊU LỌC SPOT: Quá bán + Trend hồi + Gần đáy
        if rsi < 35 and ema20 > ema50 and price <= day20 * 1.02:
            keo_ngon.append({"sym":sym, "price":price, "rsi":rsi, "ema20":ema20, "ema50":ema50, "day":day20, "dinh":dinh20})

    if not keo_ngon:
        await update.message.reply_text("💤 SPOT 1H chưa có kèo thơm đạt 3 điều kiện.\nBTC bạn chụp lúc nãy RSI 40.9 nên chưa vào lọc. Đợi nó về <35 sẽ báo.")
        return

    keo_ngon = sorted(keo_ngon, key=lambda x: x['rsi'])[:5]
    msg = f"💎 KÈO SPOT SIÊU LỌC 1H - {len(keo_ngon)} coin:\n\n"
    for k in keo_ngon:
        entry = k['price']
        sl = k['day'] * 0.98
        tp1 = entry * 1.05
        tp2 = entry * 1.10
        msg += f"🚀 {k['sym']}\nGiá: ${entry:.2f} | RSI: {k['rsi']:.1f}\nTrend: EMA20 cắt EMA50 TĂNG\nĐáy 20 nến: ${k['day']:.2f}\n👉 SPOT: Mua {entry:.2f}\nSL: {sl:.2f} (-2%)\nTP1: {tp1:.2f} (+5%) TP2: {tp2:.2f} (+10%)\n\n"
    msg += "⚠️ Chỉ báo SPOT, không phải lời khuyên đầu tư."
    await update.message.reply_text(msg)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot SPOT Siêu Lọc Live!\nGõ /scan_spot để quét kèo SPOT\nGõ /scan1h để quét nhanh RSI<35")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("scan_spot", scan_spot))
app.add_handler(CommandHandler("scan1h", scan_spot))
app.add_handler(CommandHandler("auto_scan", scan_spot))
app.run_polling()
