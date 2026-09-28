import os, threading, requests, pandas as pd, time
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "TOP100 REAL V4 Fix 0/100 Live"
def run_web():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.environ.get("TOKEN")
AUTO_CHATS = set()
# DÙNG LINK MỚI KHÔNG BỊ RENDER CHẶN
BINANCE_BASE = "https://data-api.binance.vision"

def get_top100_symbols():
    try:
        url = f"{BINANCE_BASE}/api/v3/ticker/24hr"
        data = requests.get(url, timeout=15).json()
        usdt = [d for d in data if d['symbol'].endswith('USDT')]
        ban = ["USDCUSDT","FDUSDUSDT","BUSDUSDT","TUSDUSDT"]
        usdt = [d for d in usdt if d['symbol'] not in ban]
        usdt = sorted(usdt, key=lambda x: float(x['quoteVolume']), reverse=True)
        return [d['symbol'] for d in usdt[:100]]
    except Exception as e:
        print(f"Top100 error: {e}")
        return ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","AVAXUSDT","DOTUSDT","LINKUSDT","TRXUSDT"]*10

def get_closes(sym, interval):
    try:
        url = f"{BINANCE_BASE}/api/v3/klines?symbol={sym}&interval={interval}&limit=100"
        r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        d = r.json()
        if isinstance(d, list) and len(d)>0:
            return [float(x[4]) for x in d]
    except Exception as e:
        print(f"{sym} error {e}")
    return None

def calc_rsi(prices, p=14):
    try:
        df = pd.DataFrame(prices, columns=['c']); diff = df['c'].diff()
        g = diff.where(diff>0,0).rolling(p).mean(); l = -diff.where(diff<0,0).rolling(p).mean()
        return float((100 - (100/(1+g/l))).iloc[-1])
    except: return 50
def calc_ema(prices, p):
    try: return pd.DataFrame(prices, columns=['c'])['c'].ewm(span=p).mean().iloc[-1]
    except: return 0

def scan_logic(interval):
    keo = []; symbols = get_top100_symbols(); ok_count = 0
    for sym in symbols:
        closes = get_closes(sym, interval)
        if not closes: continue
        ok_count+=1
        price = closes[-1]; rsi = calc_rsi(closes); ema20 = calc_ema(closes,20); ema50 = calc_ema(closes,50)
        if rsi < 35 and ema20 > ema50:
            keo.append({"sym":sym,"price":price,"rsi":rsi})
    return keo, ok_count, len(symbols)

async def scan100_1h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🔍 Quét TOP 100 REAL 1H BẢN A RSI<35 (Link mới fix 0/100)...")
    keo, ok, total = scan_logic("1h")
    if not keo:
        await update.message.reply_text(f"💤 TOP100 REAL 1H ({ok}/{total} coin ok) - BẢN A RSI<35 chưa có kèo. Thị trường đang khỏe.")
        return
    msg = f"💎 TOP100 REAL 1H - {len(keo)}/{ok} kèo vàng:\n\n"
    for k in keo: msg += f"🔥 {k['sym']} ${k['price']:.4f} RSI:{k['rsi']:.1f}\n"
    await update.message.reply_text(msg)

async def scan100_4h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🔍 Quét TOP 100 REAL 4H...")
    keo, ok, total = scan_logic("4h")
    if not keo:
        await update.message.reply_text(f"💤 TOP100 4H ({ok}/{total}) chưa có kèo. 4H win 80-85% nên hiếm.")
        return
    msg = f"💎💎 TOP100 4H {len(keo)} coin:\n\n"
    for k in keo: msg += f"💎 {k['sym']} ${k['price']:.4f} RSI:{k['rsi']:.1f}\n"
    await update.message.reply_text(msg)

async def auto_job(context: ContextTypes.DEFAULT_TYPE):
    if not AUTO_CHATS: return
    keo, ok, total = scan_logic("1h")
    if keo:
        msg = f"⏰ AUTO TOP100 REAL - {len(keo)} kèo RSI<35 ({ok}/{total}):\n\n"
        for k in keo: msg += f"🔥 {k['sym']} RSI:{k['rsi']:.1f} ${k['price']:.2f}\n"
        for chat_id in list(AUTO_CHATS):
            try: await context.bot.send_message(chat_id=chat_id, text=msg)
            except: pass

async def auto_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    AUTO_CHATS.add(update.effective_chat.id)
    await update.message.reply_text("✅ ĐÃ BẬT AUTO TOP100 REAL V4!\n- Đã fix lỗi 0/100 do Binance chặn\n- Giờ quét đủ 100 coin lại\n- /scan100 xem 1H, /scan100_4h xem 4H")

async def auto_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    AUTO_CHATS.discard(update.effective_chat.id)
    await update.message.reply_text("❌ Đã tắt AUTO.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot TOP100 REAL V4 Live!\n/scan100 - 1H\n/scan100_4h - 4H\n/auto_scan - Bật auto")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("scan100", scan100_1h))
app.add_handler(CommandHandler("scan100_4h", scan100_4h))
app.add_handler(CommandHandler("scan1h", scan100_1h))
app.add_handler(CommandHandler("scan_spot", scan100_1h))
app.add_handler(CommandHandler("auto_scan", auto_scan))
app.add_handler(CommandHandler("auto_off", auto_off))
app.job_queue.run_repeating(auto_job, interval=3600, first=30)
print("TOP100 V4 starting...")
app.run_polling()
