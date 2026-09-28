import os, threading, requests, time
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("TOKEN")
app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "TOP30 RSI BREAKOUT Bot Running!"

# TOP 30 vốn hóa lớn nhất - dùng USDT Binance
TOP30_SYMBOLS = [
    "BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","ADAUSDT",
    "AVAXUSDT","SHIBUSDT","DOTUSDT","LINKUSDT","TRXUSDT","MATICUSDT","LTCUSDT",
    "BCHUSDT","UNIUSDT","XLMUSDT","ETCUSDT","FILUSDT","APTUSDT","ATOMUSDT",
    "HBARUSDT","NEARUSDT","OPUSDT","ARBUSDT","VETUSDT","MKRUSDT","RNDRUSDT",
    "INJUSDT","ONDOUSDT"
]
LAST_ALERT = {} # tránh spam

def get_ohlc(symbol, interval="1H", limit=100):
    try:
        bar = "1H" if interval=="1H" else "4H" if interval=="4H" else "1D"
        url = f"https://www.okx.com/api/v5/market/candles?instId={symbol.replace('USDT','-USDT')}&bar={bar}&limit={limit}"
        r = requests.get(url, timeout=10).json()
        if 'data' not in r: return None
        data = r['data'][::-1]
        closes = [float(x[4]) for x in data]
        highs = [float(x[2]) for x in data]
        lows = [float(x[3]) for x in data]
        vols = [float(x[5]) for x in data]
        return closes, highs, lows, vols
    except: return None

def calc_rsi(closes, period=14):
    gains = [max(closes[i]-closes[i-1],0) for i in range(1,len(closes))]
    losses = [max(closes[i-1]-closes[i],0) for i in range(1,len(closes))]
    if len(gains) < period: return 50
    avg_gain = sum(gains[-period:])/period
    avg_loss = sum(losses[-period:])/period or 0.00001
    rs = avg_gain/avg_loss
    return 100 - (100/(1+rs))

def calc_ema(closes, period):
    if len(closes) < period: return closes[-1]
    return sum(closes[-period:])/period

def analyze_coin(symbol, tf="4H"):
    data = get_ohlc(symbol, tf, 100)
    if not data: return None
    closes, highs, lows, vols = data
    price = closes[-1]
    rsi = calc_rsi(closes)
    ema20 = calc_ema(closes, 20)
    ema50 = calc_ema(closes, 50)
    ema200 = calc_ema(closes, 100) if len(closes)>=100 else ema50

    # Breakout: giá phá đỉnh 20 nến gần nhất + vol tăng
    recent_high = max(highs[-21:-1])
    recent_low = min(lows[-21:-1])
    avg_vol = sum(vols[-20:-1])/19 if len(vols)>20 else vols[-1]
    vol_surge = vols[-1] > avg_vol * 1.8

    signal = []
    if rsi < 30: signal.append(f"🟢 RSI {rsi:.1f} QUÁ BÁN - Sắp hồi")
    elif rsi > 70: signal.append(f"🔴 RSI {rsi:.1f} QUÁ MUA - Coi chừng xả")

    if ema20 > ema50 and closes[-2] < calc_ema(closes[:-1], 50):
        signal.append(f"🟢 EMA20 cắt lên EMA50 - GOLDEN CROSS")
    if ema20 < ema50 and closes[-2] > calc_ema(closes[:-1], 50):
        signal.append(f"🔴 EMA20 cắt xuống EMA50 - DEATH CROSS")

    if price > recent_high and vol_surge:
        signal.append(f"🚀 BREAKOUT ĐỈNH 20 nến ${recent_high:.4f} + Vol x{vols[-1]/avg_vol:.1f}")
    if price < recent_low and vol_surge:
        signal.append(f"💥 BREAKDOWN ĐÁY 20 nến ${recent_low:.4f}")

    trend = "TĂNG" if ema20 > ema50 > ema200 else "GIẢM" if ema20 < ema50 else "SIDEWAY"
    return price, rsi, ema20, ema50, trend, signal, recent_high, recent_low

# --- COMMANDS ---
async def start_cmd(update, context):
    await update.message.reply_text(
        "🤖 BOT TOP 30 RSI + BREAKOUT PRO\nKhông cần TradingView\n\n"
        "Lệnh:\n/top30 - xem list 30 coin\n/scan - quét ngay TOP 30 (4H)\n/scan1h - quét khung 1H\n/rsi BTC - xem BTC chi tiết\n/breakout SOL - xem breakout\n\nAUTO:\n/auto_scan - tự quét 15p/lần\n/clearall - tắt hết auto"
    )

async def top30_cmd(update, context):
    msg = "📊 TOP 30 COIN VỐN HÓA LỚN:\n\n"
    for i, s in enumerate(TOP30_SYMBOLS, 1):
        msg += f"{i}. {s.replace('USDT','')}\n"
        if i % 10 == 0: msg += "\n"
    await update.message.reply_text(msg)

async def scan_cmd(update, context):
    tf = "1H" if "1h" in update.message.text.lower() else "4H"
    await update.message.reply_text(f"⏳ Đang quét {len(TOP30_SYMBOLS)} coin khung {tf} - RSI + EMA + Breakout...")
    found = []
    for symbol in TOP30_SYMBOLS:
        try:
            res = analyze_coin(symbol, tf)
            if not res: continue
            price, rsi, ema20, ema50, trend, signals, rh, rl = res
            if signals: # chỉ báo coin có tín hiệu
                txt = f"🔔 {symbol} ${price:.4f} RSI:{rsi:.1f} Trend:{trend}\n" + "\n".join(signals) + "\n"
                found.append(txt)
            time.sleep(0.3) # tránh bị rate limit
        except: continue

    if not found:
        await update.message.reply_text(f"✅ Quét xong {tf} - TOP 30 đang SIDEWAY, chưa có tín hiệu mạnh.")
    else:
        msg = f"🚨 TÍN HIỆU {tf} TOP 30 ({len(found)} coin):\n\n" + "\n".join(found[:10])
        if len(found) > 10: msg += f"\n...và {len(found)-10} tín hiệu khác"
        await update.message.reply_text(msg[:4000])

async def rsi_cmd(update, context):
    coin = "BTC"
    if context.args: coin = context.args[0].upper()
    symbol = coin + "USDT" if "USDT" not in coin else coin
    await update.message.reply_text(f"⏳ Đang tính RSI + EMA {symbol}...")
    res = analyze_coin(symbol, "4H")
    if not res: await update.message.reply_text("Không lấy được dữ liệu"); return
    price, rsi, ema20, ema50, trend, signals, rh, rl = res
    msg = (f"📈 {symbol} 4H\n💰 Giá: ${price:.4f}\n📊 RSI: {rsi:.1f}\n"
           f"EMA20: ${ema20:.4f}\nEMA50: ${ema50:.4f}\nTrend: {trend}\n"
           f"Đỉnh 20 nến: ${rh:.4f}\nĐáy 20 nến: ${rl:.4f}\n\n")
    if signals: msg += "\n".join(signals)
    else: msg += "⚪ Chưa có tín hiệu đột biến - Đang đi ngang"
    await update.message.reply_text(msg)

async def auto_scan_job(context):
    tf = "4H"
    for symbol in TOP30_SYMBOLS:
        try:
            res = analyze_coin(symbol, tf)
            if not res: continue
            price, rsi, ema20, ema50, trend, signals, rh, rl = res
            if not signals: continue
            key = f"{symbol}_{signals[0][:20]}"
            if key in LAST_ALERT and time.time() - LAST_ALERT[key] < 3600: continue
            LAST_ALERT[key] = time.time()
            txt = f"🚨 AUTO {tf} {symbol} ${price:.4f}\n" + "\n".join(signals)
            await context.bot.send_message(chat_id=context.job.chat_id, text=txt)
            time.sleep(0.5)
        except: continue

async def auto_scan_cmd(update, context):
    chat_id = update.effective_chat.id
    jobs = context.job_queue.get_jobs_by_name(f"scan_{chat_id}")
    if jobs:
        for j in jobs: j.schedule_removal()
        await update.message.reply_text("Đã TẮT auto scan TOP 30"); return
    context.job_queue.run_repeating(auto_scan_job, interval=900, first=10, chat_id=chat_id, name=f"scan_{chat_id}")
    await update.message.reply_text("Đã BẬT auto scan TOP 30 - 15p/quét - Báo RSI quá mua/bán + Breakout!")

async def clearall_cmd(update, context):
    chat_id = update.effective_chat.id
    total = 0
    for name in [f"scan_{chat_id}"]:
        for j in context.job_queue.get_jobs_by_name(name):
            j.schedule_removal(); total+=1
    await update.message.reply_text(f"🧹 Đã tắt {total} auto scan" if total else "Không có auto nào chạy")

def run_flask(): app_flask.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("top30", top30_cmd))
    app.add_handler(CommandHandler("scan", scan_cmd))
    app.add_handler(CommandHandler("scan1h", scan_cmd))
    app.add_handler(CommandHandler("rsi", rsi_cmd))
    app.add_handler(CommandHandler("breakout", rsi_cmd))
    app.add_handler(CommandHandler("auto_scan", auto_scan_cmd))
    app.add_handler(CommandHandler("clearall", clearall_cmd))
    print("TOP30 RSI BREAKOUT starting...")
    app.run_polling(stop_signals=None, close_loop=False)
