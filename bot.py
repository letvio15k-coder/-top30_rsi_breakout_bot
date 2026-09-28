import os, threading, requests, pandas as pd
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "TOP100 V5.2 FIX PEPE Live"
def run_web():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.environ.get("TOKEN")
AUTO_CHATS = set()
BINANCE_BASE = "https://data-api.binance.vision"

def fmt(p):
    # Fix triệt để PEPE/SHIB/VTHO không bao giờ $0.0000 nữa
    if p == 0: return "$0"
    if p < 0.00001:
        return f"${p:.10f}".rstrip('0').rstrip('.') # PEPE: $0.00000321
    if p < 0.001:
        return f"${p:.8f}".rstrip('0').rstrip('.')
    if p < 1:
        return f"${p:.6f}".rstrip('0').rstrip('.')
    return f"${p:.4f}"

def get_top100_symbols():
    try:
        url = f"{BINANCE_BASE}/api/v3/ticker/24hr"
        data = requests.get(url, timeout=15).json()
        usdt = [d for d in data if d['symbol'].endswith('USDT')]
        ban = ["USDCUSDT","FDUSDUSDT","BUSDUSDT","TUSDUSDT"]
        usdt = [d for d in usdt if d['symbol'] not in ban]
        usdt = sorted(usdt, key=lambda x: float(x['quoteVolume']), reverse=True)
        return [d['symbol'] for d in usdt[:100]]
    except:
        return ["BTCUSDT","ETHUSDT","XRPUSDT","DOGEUSDT","PEPEUSDT","SHIBUSDT","PHAUSDT","NILUSDT","VTHOUSDT","INJUSDT","BCHUSDT","XLMUSDT"]*9

def get_closes(sym, interval):
    try:
        url = f"{BINANCE_BASE}/api/v3/klines?symbol={sym}&interval={interval}&limit=100"
        r = requests.get(url, timeout=15)
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
        ok+=1; price = closes[-1]; rsi = calc_rsi(closes)
        if rsi < 35 and calc_ema(closes,20) > calc_ema(closes,50):
            keo.append({"sym":sym,"price":price,"rsi":rsi})
    return sorted(keo, key=lambda x: x['rsi'])[:10], ok, len(symbols)

async def scan100_1h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Quét TOP100 1H...")
    keo, ok, total = scan_logic("1h")
    if not keo:
        await update.message.reply_text(f"💤 1H ({ok}/{total}) chưa có kèo.")
        return
    msg = f"💎 TOP100 1H {len(keo)}/{ok} kèo:\n\n"
    for k in keo:
        e=k['price']; msg+=f"🔥 {k['sym']} RSI:{k['rsi']:.1f}\nEntry: {fmt(e)} SL: {fmt(e*0.97)} TP1: {fmt(e*1.06)} TP2: {fmt(e*1.12)}\n\n"
    await update.message.reply_text(msg)

async def scan100_4h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Quét TOP100 4H KIM CƯƠNG...")
    keo, ok, total = scan_logic("4h")
    if not keo:
        await update.message.reply_text(f"💤 4H ({ok}/{total}) chưa có kèo.")
        return
    msg = f"💎💎 TOP100 4H {len(keo)}/{ok} KÈO:\n\n"
    for k in keo:
        e=k['price']; msg+=f"💎 {k['sym']} RSI:{k['rsi']:.1f}\nEntry: {fmt(e)}\nSL: {fmt(e*0.97)} (-3%)\nTP1: {fmt(e*1.10)} (+10%) TP2: {fmt(e*1.20)} (+20%)\n\n"
    await update.message.reply_text(msg)

async def auto_job(context: ContextTypes.DEFAULT_TYPE):
    if not AUTO_CHATS: return
    keo, ok, _ = scan_logic("1h")
    if keo:
        msg = f"⏰ AUTO {len(keo)} KÈO:\n\n"
        for k in keo: msg+=f"🔥 {k['sym']} RSI:{k['rsi']:.1f} Entry {fmt(k['price'])}\n"
        for cid in list(AUTO_CHATS):
            try: await context.bot.send_message(chat_id=cid, text=msg)
            except: pass

async def auto_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    AUTO_CHATS.add(update.effective_chat.id)
    await update.message.reply_text("✅ AUTO V5.2 ON - Fix $0.0000 xong!\n/scan100_4h lại đi")
async def auto_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    AUTO_CHATS.discard(update.effective_chat.id)
    await update.message.reply_text("❌ Tắt AUTO")
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("V5.2 Live!\n/scan100\n/scan100_4h")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("scan100", scan100_1h))
app.add_handler(CommandHandler("scan100_4h", scan100_4h))
app.add_handler(CommandHandler("auto_scan", auto_scan))
app.add_handler(CommandHandler("auto_off", auto_off))
app.job_queue.run_repeating(auto_job, interval=3600, first=30)
app.run_polling()
