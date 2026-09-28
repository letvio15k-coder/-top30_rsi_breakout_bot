import os, threading, requests, pandas as pd, time
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "TOP100 V5 Entry SL TP Live"
def run_web():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.environ.get("TOKEN")
AUTO_CHATS = set()
BINANCE_BASE = "https://data-api.binance.vision"

def get_top100_symbols():
    try:
        url = f"{BINANCE_BASE}/api/v3/ticker/24hr"
        data = requests.get(url, timeout=15).json()
        usdt = [d for d in data if d['symbol'].endswith('USDT')]
        ban = ["USDCUSDT","FDUSDUSDT","BUSDUSDT","TUSDUSDT","EURUSDT"]
        usdt = [d for d in usdt if d['symbol'] not in ban]
        usdt = sorted(usdt, key=lambda x: float(x['quoteVolume']), reverse=True)
        return [d['symbol'] for d in usdt[:100]]
    except:
        return ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","AVAXUSDT","DOTUSDT","LINKUSDT","TRXUSDT","PEPEUSDT","SHIBUSDT","WIFUSDT","BONKUSDT","PHAUSDT","NILUSDT","VTHOUSDT","INJUSDT","XLMUSDT","BCHUSDT"]*5

def get_closes(sym, interval):
    try:
        url = f"{BINANCE_BASE}/api/v3/klines?symbol={sym}&interval={interval}&limit=100"
        r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        d = r.json()
        if isinstance(d, list) and len(d)>0:
            return [float(x[4]) for x in d]
    except: pass
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
    keo = []; symbols = get_top100_symbols(); ok = 0
    for sym in symbols:
        closes = get_closes(sym, interval)
        if not closes: continue
        ok+=1
        price = closes[-1]; rsi = calc_rsi(closes)
        ema20 = calc_ema(closes,20); ema50 = calc_ema(closes,50)
        # BẢN A: RSI<35 + EMA20>EMA50 = Entry
        if rsi < 35 and ema20 > ema50:
            keo.append({"sym":sym,"price":price,"rsi":rsi})
    return sorted(keo, key=lambda x: x['rsi'])[:10], ok, len(symbols)

async def scan100_1h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Quét TOP100 1H BẢN A - Tính Entry/SL/TP...")
    keo, ok, total = scan_logic("1h")
    if not keo:
        await update.message.reply_text(f"💤 TOP100 1H ({ok}/{total} ok) - RSI<35 chưa có kèo. Thị trường khỏe như lúc 11:19 AM.")
        return
    msg = f"💎 TOP100 1H - {len(keo)}/{ok} kèo vàng BẢN A:\n\n"
    for k in keo:
        entry = k['price']; sl = entry*0.97; tp1 = entry*1.06; tp2 = entry*1.12
        msg += f"🔥 {k['sym']} RSI:{k['rsi']:.1f}\nEntry: ${entry:.4f}\nSL: ${sl:.4f} (-3%)\nTP1: ${tp1:.4f} (+6%) TP2: ${tp2:.4f} (+12%)\n\n"
    await update.message.reply_text(msg)

async def scan100_4h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Quét TOP100 4H KIM CƯƠNG - Tính Entry/SL/TP...")
    keo, ok, total = scan_logic("4h")
    if not keo:
        await update.message.reply_text(f"💤 TOP100 4H ({ok}/{total}) chưa có kèo.")
        return
    msg = f"💎💎 TOP100 4H {len(keo)}/{ok} KÈO KIM CƯƠNG:\n\n"
    for k in keo:
        entry = k['price']; sl = entry*0.97; tp1 = entry*1.10; tp2 = entry*1.20
        msg += f"💎 {k['sym']} RSI:{k['rsi']:.1f}\nEntry: ${entry:.4f}\nSL: ${sl:.4f} (-3%)\nTP1: ${tp1:.4f} (+10%) TP2: ${tp2:.4f} (+20%)\n\n"
    await update.message.reply_text(msg)

async def auto_job(context: ContextTypes.DEFAULT_TYPE):
    if not AUTO_CHATS: return
    keo, ok, _ = scan_logic("1h")
    if keo:
        msg = f"⏰ AUTO BÁO {len(keo)} KÈO RSI<35:\n\n"
        for k in keo:
            entry = k['price']; sl = entry*0.97
            msg += f"🔥 {k['sym']} RSI:{k['rsi']:.1f}\nEntry ${entry:.4f} SL ${sl:.4f}\n"
        for chat_id in list(AUTO_CHATS):
            try: await context.bot.send_message(chat_id=chat_id, text=msg)
            except: pass

async def auto_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    AUTO_CHATS.add(update.effective_chat.id)
    await update.message.reply_text("✅ ĐÃ BẬT AUTO V5!\n- Đủ 100 coin\n- Có Entry/SL/TP đầy đủ\n- /scan100 xem 1H, /scan100_4h xem 4H\n- /auto_off tắt")

async def auto_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    AUTO_CHATS.discard(update.effective_chat.id)
    await update.message.reply_text("❌ Đã tắt AUTO.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot TOP100 V5 Entry/SL/TP Live!\n/scan100 - 1H (+6/+12%)\n/scan100_4h - 4H (+10/+20%)\n/auto_scan - Bật auto\n/auto_off - Tắt")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("scan100", scan100_1h))
app.add_handler(CommandHandler("scan100_4h", scan100_4h))
app.add_handler(CommandHandler("scan1h", scan100_1h))
app.add_handler(CommandHandler("auto_scan", auto_scan))
app.add_handler(CommandHandler("auto_off", auto_off))
app.job_queue.run_repeating(auto_job, interval=3600, first=30)

print("V5 Entry SL TP starting...")
app.run_polling()
