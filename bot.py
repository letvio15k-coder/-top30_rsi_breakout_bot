import os, threading, requests, pandas as pd
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot TOP100 SPOT A Live"
def run_web(): flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.environ.get("TOKEN")

# LẤY TOP 100 VỐN HÓA TỰ ĐỘNG TỪ COINGECKO
def get_top100_symbols():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"
        data = requests.get(url, timeout=15).json()
        symbols = []
        for coin in data:
            sym = coin['symbol'].upper() + "USDT"
            # Bỏ stable coin
            if sym in ["USDTUSDT","USDCUSDT","DAIUSDT","FDUSDUSDT"]: continue
            symbols.append(sym)
        return symbols[:100]
    except:
        # Fallback nếu CoinGecko lỗi
        return ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","AVAXUSDT","DOTUSDT","LINKUSDT","TRXUSDT","MATICUSDT","LTCUSDT","BCHUSDT","UNIUSDT","ATOMUSDT","ETCUSDT","FILUSDT","NEARUSDT","APTUSDT","ARBUSDT","OPUSDT","SUIUSDT","INJUSDT","STXUSDT","HBARUSDT","VETUSDT","ICPUSDT","QNTUSDT","XLMUSDT","ADAUSDT","PEPEUSDT","SHIBUSDT","RENDERUSDT","WIFUSDT","ARBUSDT","STXUSDT","IMXUSDT","FETUSDT","TAOUSDT","GRTUSDT","AAVEUSDT","RNDRUSDT","MKRUSDT","RUNEUSDT","BONKUSDT","JUPUSDT","ONDOUSDT","ENAUSDT","STRKUSDT"]

def get_closes(sym):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=100"
        data = requests.get(url, timeout=10).json()
        if isinstance(data, list):
            return [float(x[4]) for x in data]
        return None
    except: return None

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
    await update.message.reply_text("🔍 Đang lấy TOP 100 vốn hóa + siêu lọc BẢN A RSI<35...")
    TOP100 = get_top100_symbols()
    keo_vang = []
    for sym in TOP100:
        closes = get_closes(sym)
        if not closes: continue
        price = closes[-1]
        rsi = calc_rsi(closes)
        ema20 = calc_ema(closes, 20)
        ema50 = calc_ema(closes, 50)
        if rsi < 35 and ema20 > ema50:
            keo_vang.append({"sym":sym, "price":price, "rsi":rsi})

    if not keo_vang:
        await update.message.reply_text(f"💤 TOP 100 vừa quét xong ({len(TOP100)} coin) - BẢN A RSI<35 chưa có kèo.\nThị trường đang khỏe, đợi 1-2h nữa gõ lại /scan100")
        return

    keo_vang = sorted(keo_vang, key=lambda x: x['rsi'])[:7]
    msg = f"💎💎 KÈO VÀNG TOP 100 - BẢN A RSI<35 ({len(keo_vang)}/100 coin):\n\n"
    for k in keo_vang:
        e = k['price']
        sl = e * 0.97
        tp1 = e * 1.06
        tp2 = e * 1.12
        msg += f"🔥 {k['sym']} ${e:.4f} RSI:{k['rsi']:.1f}\nMua SPOT: {e:.4f} | SL {sl:.4f} (-3%) TP1 +6% TP2 +12%\n\n"
    await update.message.reply_text(msg)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot TOP 100 BẢN A Live!\n/scan100 - Quét 100 coin vốn hóa lớn\n/scan_spot - Quét nhanh\n/auto_scan - Bật auto mỗi giờ")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("scan100", scan_spot))
app.add_handler(CommandHandler("scan_spot", scan_spot))
app.add_handler(CommandHandler("scan1h", scan_spot))
app.add_handler(CommandHandler("auto_scan", scan_spot))
app.run_polling()
