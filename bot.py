import requests
import time
import csv
import os
from datetime import datetime

prices = []

balance_usdt = 1000
btc = 0
in_position = False
buy_price = 0

stop_loss = 0.0003      # 0.03%
take_profit = 0.0003    # 0.03%

CSV_FILE = "trades.csv"
URL = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"


# =========================
# CSV SETUP
# =========================
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Time",
            "Price",
            "Action",
            "Profit",
            "Balance",
            "Trend",
            "CHOCH",
            "FVG",
            "Strategy"
        ])


def save_trade(price, action, profit, balance, trend, choch, fvg, strategy):
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            price,
            action,
            profit,
            balance,
            trend,
            choch,
            fvg,
            strategy
        ])


# =========================
# FETCH PRICE
# =========================
def get_price():
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data["price"])
    except Exception as e:
        print("Error fetching price:", e)
        return None


# =========================
# STRATEGY FUNCTIONS
# =========================
def detect_trend(prices):
    if len(prices) < 20:
        return "RANGE"

    short_ma = sum(prices[-5:]) / 5
    long_ma = sum(prices[-20:]) / 20

    diff_percent = (short_ma - long_ma) / long_ma

    if diff_percent > 0.0001:
        return "UP"
    elif diff_percent < -0.0001:
        return "DOWN"
    else:
        return "RANGE"


def detect_choch(prices, trend):
    if len(prices) < 12:
        return None

    old_high = max(prices[-12:-6])
    old_low = min(prices[-12:-6])

    recent_high = max(prices[-6:])
    recent_low = min(prices[-6:])

    if trend == "DOWN" and recent_high > old_high:
        return "BULLISH"

    if trend == "UP" and recent_low < old_low:
        return "BEARISH"

    return None


def detect_fvg(prices):
    """
    ملاحظة:
    هادي FVG بسيطة بزاف حيث عندنا غير price ticks.
    FVG الحقيقية خاصها candles OHLC.
    """
    if len(prices) < 3:
        return None

    p1 = prices[-3]
    p2 = prices[-2]
    p3 = prices[-1]

    move = abs(p3 - p1) / p1

    # حركة قوية طالعة
    if p1 < p2 < p3 and move > 0.0002:
        return "BULLISH"

    # حركة قوية هابطة
    if p1 > p2 > p3 and move > 0.0002:
        return "BEARISH"

    return None


# =========================
# MAIN LOOP
# =========================
while True:
    price = get_price()

    if price is None:
        time.sleep(5)
        continue

    prices.append(price)

    trend = detect_trend(prices)
    choch = detect_choch(prices, trend)
    fvg = detect_fvg(prices)

    print("Price:", price)
    print("Count:", len(prices))
    print("Trend:", trend)
    print("CHOCH:", choch)
    print("FVG:", fvg)

    if len(prices) >= 20:
        short_ma = sum(prices[-3:]) / 3
        long_ma = sum(prices[-5:]) / 5

        print("Short MA:", short_ma)
        print("Long MA:", long_ma)

        buy_signal = False
        strategy = "WAIT"

        # =========================
        # BUY LOGIC
        # =========================

        # Strategy 1: old MA strategy
        if short_ma > long_ma and trend == "UP":
            buy_signal = True
            strategy = "MA_TREND_UP"

        # Strategy 2: CHOCH + FVG
        if choch == "BULLISH" and fvg == "BULLISH":
            buy_signal = True
            strategy = "CHOCH_FVG_BUY"

        if buy_signal and not in_position:
            btc = balance_usdt / price
            balance_usdt = 0
            in_position = True
            buy_price = price

            print("BUY")
            print("Strategy:", strategy)

            save_trade(
                price=price,
                action="BUY",
                profit="",
                balance=balance_usdt,
                trend=trend,
                choch=choch,
                fvg=fvg,
                strategy=strategy
            )

        # =========================
        # SELL LOGIC TP / SL
        # =========================
        elif in_position:
            profit_percent = (price - buy_price) / buy_price
            print("Profit %:", round(profit_percent * 100, 4), "%")

            # Take Profit
            if profit_percent >= take_profit:
                profit = (price - buy_price) * btc
                balance_usdt = btc * price
                btc = 0
                in_position = False

                print("SELL TAKE PROFIT")
                print("Profit:", round(profit, 2))

                save_trade(
                    price=price,
                    action="SELL_TP",
                    profit=round(profit, 4),
                    balance=round(balance_usdt, 4),
                    trend=trend,
                    choch=choch,
                    fvg=fvg,
                    strategy="TAKE_PROFIT"
                )

            # Stop Loss
            elif profit_percent <= -stop_loss:
                profit = (price - buy_price) * btc
                balance_usdt = btc * price
                btc = 0
                in_position = False

                print("SELL STOP LOSS")
                print("Profit:", round(profit, 2))

                save_trade(
                    price=price,
                    action="SELL_SL",
                    profit=round(profit, 4),
                    balance=round(balance_usdt, 4),
                    trend=trend,
                    choch=choch,
                    fvg=fvg,
                    strategy="STOP_LOSS"
                )

    print("------")
    time.sleep(5)
