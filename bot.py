import os, threading, requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "V5.6 Live"
def run_web(): flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.environ.get("TOKEN")
BINANCE = "https://data-api.binance.vision"

def fmt(p):
 try:
  p=float(p)
  if p<0.00001: return f"${p:.10f}".rstrip('0').rstrip('.')
  if p<0.001: return f"${p:.8f}".rstrip('0').rstrip('.')
  if p<1: return f"${p:.6f}".rstrip('0').rstrip('.')
  return f"${p:.4f}"
 except: return str(p)

def calc_rsi(c,p=14):
 g=l=0
 for i in range(1,p+1):
  d=c[-i]-c[-i-1]
  g+=d if d>0 else 0
  l-=d if d<0 else 0
 return 100-(100/(1+g/l)) if l!=0 else 100

def scan():
 keo=[]
 try:
  data=requests.get(f"{BINANCE}/api/v3/ticker/24hr",timeout=15).json()
  usdt=sorted([d for d in data if d['symbol'].endswith('USDT')],key=lambda x:float(x['quoteVolume']),reverse=True)[:100]
  for d in usdt:
   try:
    kl=requests.get(f"{BINANCE}/api/v3/klines?symbol={d['symbol']}&interval=4h&limit=50",timeout=8).json()
    closes=[float(x[4]) for x in kl]
    if len(closes)<30: continue
    rsi=calc_rsi(closes)
    ema20=sum(closes[-20:])/20
    ema50=sum(closes[-50:])/50
    if rsi<35 and ema20>ema50: keo.append((d['symbol'],rsi,closes[-1]))
   except: continue
  keo=sorted(keo,key=lambda x:x[1])[:10]
 except: pass
 return keo

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
 await update.message.reply_text("Bot V5.6 Live\n/scan = quet TOP100 RSI<35\n/scan100_4h = y chang\n/auto_scan = quet\n/menu = huong dan")

async def quet_func(update:Update,context:ContextTypes.DEFAULT_TYPE):
 await update.message.reply_text("Dang quet TOP100 4H...")
 keo=scan()
 if not keo:
  await update.message.reply_text("0/100 coin co RSI<35 luc nay (Golden Cross)")
  return
 msg=f"💎 TOP {len(keo)} KEO RSI<35 4H (Golden Cross):\n\n"
 for s,r,p in keo:
  msg+=f"💎 {s} RSI:{r:.1f}\nEntry: {fmt(p)}\nSL: {fmt(p*0.97)} (-3%)\nTP1: {fmt(p*1.10)} (+10%) TP2: {fmt(p*1.20)} (+20%)\n\n"
 await update.message.reply_text(msg)

async def error_handler(update, context): print(f"Error: {context.error}")

if __name__=="__main__":
 app=ApplicationBuilder().token(TOKEN).build()
 app.add_handler(CommandHandler("start",start))
 app.add_handler(CommandHandler("menu",start))
 app.add_handler(CommandHandler("quet",quet_func))
 app.add_handler(CommandHandler("scan",quet_func))
 app.add_handler(CommandHandler("scan100_4h",quet_func))
 app.add_handler(CommandHandler("auto_scan",quet_func))
 app.add_error_handler(error_handler)
 app.run_polling()
