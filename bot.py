import os, threading, requests, time
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "V6.3 RSI30 70COINS FIXED - No JobQueue"

def run_web():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.environ.get("TOKEN") or os.environ.get("TELEGRAM_TOKEN")
BINANCE = "https://data-api.binance.vision"
CHAT_FILE = "/tmp/chats.txt"

# 70 COIN TOP/MID - KHONG STABLE - KHONG MEME
COINS = [
    "BTC","ETH","SOL","BNB","XRP","ADA","AVAX","DOT","TRX","LINK",
    "NEAR","POL","LTC","BCH","ETC","XLM","UNI","OP","ARB","SUI",
    "APT","FIL","HBAR","TAO","FET","RENDER","WLD","INJ","STX","IMX",
    "SEI","ENA","ONDO","ZEC","HYPE","AAVE","MKR","LDO","ATOM","TIA",
    "EGLD","ALGO","VET","ICP","QNT","FTM","THETA","FLOW","KAVA","ROSE",
    "MNT","STRK","METIS","PENDLE","ENS","CRV","COMP","SNX","DYDX","GMX",
    "1INCH","JUP","PYTH","W","S","AR","GRT","OCEAN","AGIX"
]
COINS = list(dict.fromkeys(COINS))

def load_chats():
    try:
        with open(CHAT_FILE,'r') as f: return set(int(x) for x in f.read().split() if x)
    except: return set()
def save_chats(s):
    try:
        with open(CHAT_FILE,'w') as f: f.write(' '.join(map(str,s)))
    except: pass
CHAT_IDS = load_chats()

def fmt(p):
    try:
        p=float(p)
        if p<0.00001: return f"${p:.10f}".rstrip('0').rstrip('.')
        if p<0.001: return f"${p:.8f}".rstrip('0').rstrip('.')
        if p<1: return f"${p:.6f}".rstrip('0').rstrip('.')
        return f"${p:.4f}"
    except: return str(p)

# --- RSI CHUAN TRADINGVIEW - WILDER ---
def calc_rsi(c, p=14):
    if len(c) < p + 1: return 50
    gains = []; losses = []
    for i in range(1, len(c)):
        diff = c[i] - c[i-1]
        gains.append(diff if diff > 0 else 0)
        losses.append(abs(diff) if diff < 0 else 0)
    avg_gain = sum(gains[:p]) / p
    avg_loss = sum(losses[:p]) / p
    for i in range(p, len(gains)):
        avg_gain = (avg_gain * (p-1) + gains[i]) / p
        avg_loss = (avg_loss * (p-1) + losses[i]) / p
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def scan():
    keo=[]
    for symbol in COINS:
        try:
            kl=requests.get(f"{BINANCE}/api/v3/klines?symbol={symbol}USDT&interval=4h&limit=100",timeout=8).json()
            if isinstance(kl, dict): continue
            closes=[float(x[4]) for x in kl]
            if len(closes)<50: continue
            rsi=calc_rsi(closes, 14)
            ema20=sum(closes[-20:])/20
            ema50=sum(closes[-50:])/50
            # DIEU KIEN MOI: RSI < 30
            if rsi < 30 and ema20 > ema50:
                keo.append((symbol, rsi, closes[-1]))
        except: continue
    keo=sorted(keo,key=lambda x:x[1])
    return keo[:10]

def auto_loop():
    while True:
        time.sleep(3600)
        keo=scan()
        if not keo or not CHAT_IDS: continue
        msg=f"⏰ AUTO {len(keo)} KEO RSI<30 4H (70 COINS):\n\n"
        for s,r,p in keo:
            msg+=f"💎 {s} RSI:{r:.1f}\nEntry:{fmt(p)} SL:{fmt(p*0.97)} TP:{fmt(p*1.15)}\n\n"
        for cid in list(CHAT_IDS):
            try:
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",json={"chat_id":cid,"text":msg},timeout=10)
            except: pass

threading.Thread(target=auto_loop, daemon=True).start()

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"V6.3 - 70 COINS MID/TOP - RSI<30\nTong {len(COINS)} coin\n/scan - quet ngay\n/auto_scan - bat auto 60p\n/stop_auto - tat")

async def quet_func(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Dang quet {len(COINS)} coin 4H RSI<30... (15-20s)")
    keo=scan()
    if not keo:
        await update.message.reply_text(f"0/{len(COINS)} coin RSI<30 - Thi truong dang nong, khong co diem mua dep")
        return
    msg=f"💎 TOP {len(keo)} KEO RSI<30 4H:\n\n"
    for s,r,p in keo:
        msg+=f"{s} RSI:{r:.1f}\nEntry:{fmt(p)} SL:{fmt(p*0.97)} TP:{fmt(p*1.15)}\n\n"
    await update.message.reply_text(msg)

async def auto_on(update:Update,context:ContextTypes.DEFAULT_TYPE):
    CHAT_IDS.add(update.effective_chat.id); save_chats(CHAT_IDS)
    await update.message.reply_text(f"Da BAT auto 60p cho {update.effective_chat.id} - Dang theo doi {len(COINS)} coin RSI<30")

async def auto_off(update:Update,context:ContextTypes.DEFAULT_TYPE):
    CHAT_IDS.discard(update.effective_chat.id); save_chats(CHAT_IDS)
    await update.message.reply_text("Da TAT auto")

if __name__=="__main__":
    app=ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("menu",start))
    app.add_handler(CommandHandler("scan",quet_func))
    app.add_handler(CommandHandler("scan100_4h",quet_func))
    app.add_handler(CommandHandler("quet",quet_func))
    app.add_handler(CommandHandler("auto_scan",auto_on))
    app.add_handler(CommandHandler("stop_auto",auto_off))
    print(f"V6.3 RSI30 70COINS RUNNING - {len(COINS)} coins")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES, close_loop=False, stop_signals=None)
