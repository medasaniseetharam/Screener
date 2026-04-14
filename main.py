import requests
import pandas as pd
import yfinance as yf
import schedule
import time

# =========================
# STEP 1: FETCH CHARTINK DATA (REAL)
# =========================


def get_chartink_stocks():
    import pandas as pd

    # ✅ Correct CSV export link
    url = "https://docs.google.com/spreadsheets/d/1bzO5HlakZWKgbWCqB30L-6t7Mk67keraKTw5DL22pxY/export?format=csv"

    try:
        df = pd.read_csv(url)

        # Clean column names
        df.columns = df.columns.str.strip()
        print("Columns:", df.columns)

        # ✅ Use correct column name
        stocks = [str(symbol).strip() +
                  ".NS" for symbol in df['NSE Code'].dropna()]

        print("Chartink Stocks:", stocks)

        return stocks

    except Exception as e:
        print("❌ Error reading sheet:", e)
        return []

# =========================
# STEP 2: YOUR BO LOGIC
# =========================


def check_breakout(stock):
    try:
        df = yf.download(stock, period="1mo", interval="1d", progress=False)

        if df.empty or len(df) < 11:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        length = 10
        volMultiplier = 1.5

        latest = df.iloc[-1]
        prev = df.iloc[:-1]

        close = float(latest['Close'])
        open_ = float(latest['Open'])
        high = float(latest['High'])
        low = float(latest['Low'])
        volume = float(latest['Volume'])

        highestHigh = float(prev['High'][-length:].max())
        avgVolume = float(prev['Volume'][-length:].mean())

        isBreakout = close > highestHigh
        isBullish = close > open_
        isHighClose = close >= (high - (high - low) * 0.25)
        isVolumeSpike = volume > avgVolume * volMultiplier

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
# STEP 3: MAIN SCAN
# =========================


def run_scan():
    print("Running scan...")

    stocks = get_chartink_stocks()
    breakout_stocks = []

    for stock in stocks:
        result = check_breakout(stock)
        if result:
            breakout_stocks.append(result)

    print("BO Stocks:", breakout_stocks)

 send_telegram(breakout_stocks)

def send_telegram(stocks):
    import requests

    token = "YOUR_BOT_TOKEN"
    chat_id = "YOUR_CHAT_ID"

    if not stocks:
        message = "❌ No Breakout Stocks Today"
    else:
        message = "🚀 BO Stocks:\n\n"
        for s in stocks:
            message += f"{s['stock']} | ₹{s['close']} | Vol: {s['volume']}\n"

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    requests.post(url, data={
        "chat_id": chat_id,
        "text": message
    })

# Run immediately for testing
run_scan()

# =========================
# STEP 5: SCHEDULE DAILY
# =========================
print("🚀 Cloud Scanner Started...")

# TEMP TEST (run every 1 min)
schedule.every(1).minutes.do(run_scan)

while True:
    schedule.run_pending()
    time.sleep(30)
