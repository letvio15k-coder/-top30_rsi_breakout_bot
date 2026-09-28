import os, threading, requests, pandas as pd
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "TOP100 FINAL Live"
def run_web(): flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.environ.get("TOKEN")
AUTO_CHATS = set() # Lưu các chat bật auto

def get_top100_symbols():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"
        data = requests.get(url, timeout=15).json()
        syms = []
        for c in data:
            s = c['symbol'].upper()+"USDT"
            if s not in ["USDTUSDT","USDCUSDT","DAIUSDT","FDUSDUSDT"]: syms.append(s)
        return syms[:100]
    except: return ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","AVAXUSDT","DOTUSDT","LINKUSDT","TRXUSDT","MATICUSDT","LTCUSDT","BCHUSDT","UNIUSDT","ATOMUSDT","ETCUSDT","FILUSDT","NEARUSDT","APTUSDT","ARBUSDT","OPUSDT","SUIUSDT","INJUSDT","STXUSDT","HBARUSDT","VETUSDT","ICPUSDT","QNTUSDT","XLMUSDT","ADAUSDT"]

def get_closes(sym, interval):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&limit=100"
        d = requests.get(url, timeout=10).json()
        if isinstance(d, list): return [float(x[4]) for x in d]
        return None
    except: return None

def calc_rsi(prices, p=14):
    df = pd.DataFrame(prices, columns=['c']); d = df['c'].diff()
    g = d.where(d>0,0).rolling(p).mean(); l = -d.where(d<0,0).rolling(p).mean()
    return float((100 - (100/(1+g/l))).iloc[-1])

def calc_ema(prices, p): return pd.DataFrame(prices, columns=['c'])['c'].ewm(span=p).mean().iloc[-1]

def scan_logic(interval):
    TOP100 = get_top100_symbols()
    keo = []
    for sym in TOP100:
        closes = get_closes(sym, interval)
        if not closes: continue
        price = closes[-1]; rsi = calc_rsi(closes); ema20 = calc_ema(closes,20); ema50 = calc_ema(closes,50)
        if rsi < 35 and ema20 > ema50:
            keo.append({"sym":sym,"price":price,"rsi":rsi})
    keo = sorted(keo, key=lambda x: x['rsi'])[:7]
    return keo

async def scan100_1h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Quét TOP 100 - 1H BẢN A RSI<35...")
    keo = scan_logic("1h")
    if not keo:
        await update.message.reply_text("💤 TOP100 1H: Chưa có kèo RSI<35. Thị trường đang khỏe.")
        return
    msg = f"💎 TOP100 1H - {len(keo)} kèo vàng:\n\n"
    for k in keo: msg += f"🔥 {k['sym']} ${k['price']:.4f} RSI:{k['rsi']:.1f} Mua SPOT SL -3% TP +6%/+12%\n\n"
    await update.message.reply_text(msg)

async def scan100_4h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Quét TOP 100 - 4H BẢN A RSI<35 (Tỉ lệ thắng cao nhất)...")
    keo = scan_logic("4h")
    if not keo:
        await update.message.reply_text("💤 TOP100 4H: Chưa có kèo. 4H hiếm hơn 1H nhưng win ~80-85%.")
        return
    msg = f"💎💎 TOP100 4H - KÈO KIM CƯƠNG {len(keo)} coin:\n\n"
    for k in keo: msg += f"💎 {k['sym']} ${k['price']:.4f} RSI:{k['rsi']:.1f} 4H QUÁ BÁN MẠNH\nMua SPOT hold 2-3 ngày TP +10-20%\n\n"
    await update.message.reply_text(msg)

async def auto_job(context: ContextTypes.DEFAULT_TYPE):
    # Job tự chạy mỗi giờ - chỉ báo khi có kèo
    for chat_id in list(AUTO_CHATS):
        keo_1h = scan_logic("1h")
        keo_4h = scan_logic("4h")
        if keo_1h:
            msg = f"⏰ AUTO TOP100 1H - Có {len(keo_1h)} kèo vàng BẢN A:\n\n"
            for k in keo_1h: msg += f"🔥 {k['sym']} RSI:{k['rsi']:.1f} ${k['price']:.2f}\n"
            try: await context.bot.send_message(chat_id=chat_id, text=msg)
            except: pass
        if keo_4h:
            msg = f"💎 AUTO TOP100 4H - KÈO KIM CƯƠNG {len(keo_4h)} coin:\n\n"
            for k in keo_4h: msg += f"💎 {k['sym']} RSI:{k['rsi']:.1f} ${k['price']:.2f}\n"
            try: await context.bot.send_message(chat_id=chat_id, text=msg)
            except: pass

async def auto_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    AUTO_CHATS.add(chat_id)
    await update.message.reply_text("✅ ĐÃ BẬT AUTO TOP100!\n- Tự quét mỗi 60 phút\n- Có kèo RSI<35 BẢN A mới báo, không có thì im (đỡ spam như ảnh 11:19 AM hôm qua)\n- Quét cả 1H + 4H\nGõ /auto_off để tắt.")

async def auto_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    AUTO_CHATS.discard(update.effective_chat.id)
    await update.message.reply_text("❌ Đã tắt AUTO.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot TOP100 FINAL Live!\n/scan100 - Quét 100 coin 1H\n/scan100_4h - Quét 100 coin 4H (win cao)\n/auto_scan - Bật tự báo mỗi giờ\n/auto_off - Tắt auto")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("scan100", scan100_1h))
app.add_handler(CommandHandler("scan100_4h", scan100_4h))
app.add_handler(CommandHandler("scan1h", scan100_1h))
app.add_handler(CommandHandler("scan_spot", scan100_1h))
app.add_handler(CommandHandler("auto_scan", auto_scan))
app.add_handler(CommandHandler("auto_off", auto_off))
# Job auto mỗi 60 phút
app.job_queue.run_repeating(auto_job, interval=3600, first=20)
app.run_polling()
