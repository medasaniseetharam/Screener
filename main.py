import requests
import pandas as pd
import yfinance as yf
import schedule
import time

# =========================
# STEP 1: FETCH CHARTINK DATA
# =========================
def get_chartink_stocks():
    url = "https://docs.google.com/spreadsheets/d/1bzO5HlakZWKgbWCqB30L-6t7Mk67keraKTw5DL22pxY/export?format=csv"

    try:
        df = pd.read_csv(url)

        df.columns = df.columns.str.strip()
        print("Columns:", df.columns)

        stocks = [str(symbol).strip() + ".NS" for symbol in df['NSE Code'].dropna()]

        print("Chartink Stocks:", stocks[:20])  # show first 20 only
        return stocks

    except Exception as e:
        print("❌ Error reading sheet:", e)
        return []

# =========================
# STEP 2: BREAKOUT LOGIC
# =========================
def check_breakout(stock):
    try:
        df = yf.download(stock, period="1mo", interval="1d", progress=False)

        if df.empty or len(df) < 11:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        latest = df.iloc[-1]
        prev = df.iloc[:-1]

        close = float(latest['Close'])
        open_ = float(latest['Open'])
        high = float(latest['High'])
        low = float(latest['Low'])
        volume = float(latest['Volume'])

        highestHigh = float(prev['High'][-10:].max())
        avgVolume = float(prev['Volume'][-10:].mean())

        isBreakout = close > highestHigh
        isBullish = close > open_
        isHighClose = close >= (high - (high - low) * 0.25)
        isVolumeSpike = volume > avgVolume * 1.5

        if isBreakout and isBullish and isHighClose and isVolumeSpike:
            return {
                "stock": stock.replace(".NS", ""),
                "close": round(close, 2),
                "volume": int(volume)
            }

        return None

    except Exception as e:
        print(f"Error in {stock}:", e)
        return None

# =========================
# STEP 3: TELEGRAM ALERT
# =========================
def send_telegram(stocks):
    token = "bot8667626238:AAE04TszgZDIZkqyiFS7cAn_uEYZuJ3OlRI"
    chat_id = "8610840272"

    if not stocks:
        message = "❌ No Breakout Stocks Today"
    else:
        message = "🚀 BO Stocks:\n\n"
        for s in stocks:
            message += f"{s['stock']} | ₹{s['close']} | Vol: {s['volume']}\n"

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        requests.post(url, data={"chat_id": chat_id, "text": message})
        print("✅ Telegram sent")
    except Exception as e:
        print("❌ Telegram error:", e)

# =========================
# STEP 4: MAIN SCAN
# =========================
def run_scan():
    print("Running scan...")

    stocks = get_chartink_stocks()
    breakout_stocks = []

    # Optional: limit for speed
    stocks = stocks[:100]

    for stock in stocks:
        result = check_breakout(stock)
        if result:
            breakout_stocks.append(result)

    print("BO Stocks:", breakout_stocks)

    send_telegram(breakout_stocks)

# =========================
# STEP 5: RUN + SCHEDULE
# =========================

print("🚀 Cloud Scanner Started...")

# 🔥 TEST MODE (every 1 min)
# schedule.every(1).minutes.do(run_scan)

# 👉 AFTER TEST, CHANGE TO:
 schedule.every().day.at("12:35").do(run_scan)

# Run once immediately
run_scan()

# Keep alive (IMPORTANT for cloud)
while True:
    schedule.run_pending()
    time.sleep(30)
