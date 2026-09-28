import os, threading, requests, pandas as pd, time
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "TOP100 FINAL Fixed Live"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    print("!!! CHUA SET TOKEN!!!")

AUTO_CHATS = set()

def get_top100_symbols():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"
        data = requests.get(url, timeout=15).json()
        syms = [c['symbol'].upper()+"USDT" for c in data if c['symbol'].upper()+"USDT" not in ["USDTUSDT","USDCUSDT"]]
        return syms[:100]
    except:
        return ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","AVAXUSDT","DOTUSDT","LINKUSDT","TRXUSDT","MATICUSDT","LTCUSDT","BCHUSDT","UNIUSDT","ATOMUSDT","ADAUSDT","PEPEUSDT","SHIBUSDT","WIFUSDT","BONKUSDT"]

def get_closes(sym, interval):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&limit=100"
        d = requests.get(url, timeout=10).json()
        if isinstance(d, list): return [float(x[4]) for x in d]
    except: pass
    return None

def calc_rsi(prices, p=14):
    try:
        df = pd.DataFrame(prices, columns=['c']); d = df['c'].diff()
        g = d.where(d>0,0).rolling(p).mean(); l = -d.where(d<0,0).rolling(p).mean()
        return float((100 - (100/(1+g/l))).iloc[-1])
    except: return 50

def calc_ema(prices, p):
    try: return pd.DataFrame(prices, columns=['c'])['c'].ewm(span=p).mean().iloc[-1]
    except: return 0

def scan_logic(interval):
    keo = []
    for sym in get_top100_symbols():
        closes = get_closes(sym, interval)
        if not closes: continue
        price = closes[-1]; rsi = calc_rsi(closes)
        ema20 = calc_ema(closes,20); ema50 = calc_ema(closes,50)
        if rsi < 35 and ema20 > ema50:
            keo.append({"sym":sym,"price":price,"rsi":rsi})
    return sorted(keo, key=lambda x: x['rsi'])[:7]

async def scan100_1h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Quét TOP100 1H BẢN A RSI<35...")
    keo = scan_logic("1h")
    if not keo:
        await update.message.reply_text("💤 TOP100 1H chưa có kèo RSI<35. Win cao nên hiếm, đợi sập sẽ có.")
        return
    msg = f"💎 TOP100 1H - {len(keo)} kèo vàng:\n\n"
    for k in keo: msg += f"🔥 {k['sym']} ${k['price']:.4f} RSI:{k['rsi']:.1f}\n"
    await update.message.reply_text(msg)

async def scan100_4h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Quét TOP100 4H - KIM CƯƠNG...")
    keo = scan_logic("4h")
    if not keo:
        await update.message.reply_text("💤 TOP100 4H chưa có kèo. 4H win 80-85% nhưng cả tuần mới có 1 lần.")
        return
    msg = f"💎💎 TOP100 4H {len(keo)} coin:\n\n"
    for k in keo: msg += f"💎 {k['sym']} ${k['price']:.4f} RSI:{k['rsi']:.1f} - Mua SPOT hold 2-3 ngày\n\n"
    await update.message.reply_text(msg)

async def auto_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    AUTO_CHATS.add(update.effective_chat.id)
    await update.message.reply_text("✅ ĐÃ BẬT AUTO TOP100!\nBot sẽ tự quét mỗi 60p, có kèo RSI<35 mới báo. Bạn gõ /scan100 để xem ngay, /scan100_4h để xem 4H.")

async def auto_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    AUTO_CHATS.discard(update.effective_chat.id)
    await update.message.reply_text("❌ Đã tắt AUTO.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot TOP100 BẢN A Fixed Live!\n/scan100 - Quét 100 coin 1H\n/scan100_4h - Quét 100 coin 4H\n/auto_scan - Bật tự báo\n/auto_off - Tắt")

# Job auto an toàn
async def auto_job(context: ContextTypes.DEFAULT_TYPE):
    if not AUTO_CHATS: return
    keo = scan_logic("1h")
    if keo:
        msg = f"⏰ AUTO BÁO KÈO {len(keo)} coin RSI<35:\n\n"
        for k in keo: msg += f"🔥 {k['sym']} RSI:{k['rsi']:.1f} ${k['price']:.2f}\n"
        for chat_id in list(AUTO_CHATS):
            try: await context.bot.send_message(chat_id=chat_id, text=msg)
            except: pass

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("scan100", scan100_1h))
app.add_handler(CommandHandler("scan100_4h", scan100_4h))
app.add_handler(CommandHandler("scan1h", scan100_1h))
app.add_handler(CommandHandler("scan_spot", scan100_1h))
app.add_handler(CommandHandler("auto_scan", auto_scan))
app.add_handler(CommandHandler("auto_off", auto_off))
app.job_queue.run_repeating(auto_job, interval=3600, first=30)

print("Bot TOP100 FIXED starting...")
app.run_polling()
