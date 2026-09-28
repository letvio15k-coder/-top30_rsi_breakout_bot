import os, threading, requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "TOP30 RSI V5.4 FIX UPDATER Live"
def run_web():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.environ.get("TOKEN")
BINANCE = "https://data-api.binance.vision"

def fmt(p):
    try:
        p=float(p)
        if p==0: return "$0"
        if p<0.00001: return f"${p:.10f}".rstrip('0').rstrip('.')
        if p<0.001: return f"${p:.8f}".rstrip('0').rstrip('.')
        if p<1: return f"${p:.6f}".rstrip('0').rstrip('.')
        return f"${p:.4f}"
    except: return str(p)

def calc_rsi(closes, period=14):
    gains=0; losses=0
    for i in range(1, period+1):
        diff = closes[-i] - closes[-i-1]
        if diff>0: gains+=diff
        else: losses-=diff
    if losses==0: return 100
    rs=gains/losses
    return 100-(100/(1+rs))

def scan():
    keo=[]
    try:
        data=requests.get(f"{BINANCE}/api/v3/ticker/24hr",timeout=10).json()
        usdt=[d for d in data if d['symbol'].endswith('USDT')]
        usdt=sorted(usdt,key=lambda x:float(x['quoteVolume']),reverse=True)[:100]
        for d in usdt:
            sym=d['symbol']
            try:
                kl=requests.get(f"{BINANCE}/api/v3/klines?symbol={sym}&interval=4h&limit=50",timeout=6).json()
                closes=[float(x[4]) for x in kl]
                if len(closes)<30: continue
                rsi=calc_rsi(closes)
                ema20=sum(closes[-20:])/20
                ema50=sum(closes[-50:])/50 if len(closes)>=50 else sum(closes)/len(closes)
                if rsi<35 and ema20>ema50:
                    keo.append((sym,rsi,closes[-1]))
            except: continue
        keo=sorted(keo,key=lambda x:x[1])[:10]
    except Exception as e:
        print(e)
    return keo

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot TOP30 RSI V5.4 Live - Gõ /quet")

async def quet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Đang quét TOP100 4H...")
    keo=scan()
    if not keo:
        await update.message.reply_text("0/100 coin, chưa có RSI<35")
        return
    msg=f"💎 TOP {len(keo)} KÈO RSI<35 4H (Golden Cross):\n\n"
    for sym,rsi,price in keo:
        msg+=f"{sym} RSI:{rsi:.1f} Entry:{fmt(price)} SL:{fmt(price*0.97)} TP1:{fmt(price*1.10)} TP2:{fmt(price*1.20)}\n"
    await update.message.reply_text(msg)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quet", quet))
    print("V5.4 starting...")
    app.run_polling()
