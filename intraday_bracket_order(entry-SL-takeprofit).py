from ib_insync import *
import pandas as pd

# === Connect to IBKR ===
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)  # Paper trading

# === Choose Stock ===
symbol = 'AAPL'
contract = Stock(symbol, 'SMART', 'USD')

# === Fetch previous day's 1-day data to determine market bias ===
yesterday_data = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='2 D',     # last 2 days
    barSizeSetting='1 day',
    whatToShow='TRADES',
    useRTH=True
)

df_hist = util.df(yesterday_data)
prev_day = df_hist.iloc[-2]  # second last bar = yesterday
prev_open = prev_day['open']
prev_close = prev_day['close']

if prev_close > prev_open:
    market_bias = 'up'
else:
    market_bias = 'down'

print(f"Yesterday: Open={prev_open}, Close={prev_close}, Market Bias={market_bias.upper()}")

# === Fetch 5-min intraday bars for today ===
intraday_bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='1 D',      # today
    barSizeSetting='5 mins',
    whatToShow='TRADES',
    useRTH=True
)

df = util.df(intraday_bars)
df['color'] = df.apply(lambda x: 'green' if x.close > x.open else 'red', axis=1)

# Ignore first 3 candles
df_after3 = df.iloc[3:]

# === Choose signal candle based on market bias ===
if market_bias == 'down':  # market down → go long on green candle
    signal_candles = df_after3[df_after3['color'] == 'green']
    trade_direction = 'BUY'
else:                     # market up → go short on red candle
    signal_candles = df_after3[df_after3['color'] == 'red']
    trade_direction = 'SELL'

if signal_candles.empty:
    print("No suitable signal candle found.")
    ib.disconnect()
    exit()

lowest_vol_candle = signal_candles.loc[signal_candles['volume'].idxmin()]
high = lowest_vol_candle['high']
low = lowest_vol_candle['low']

# === Calculate Entry, Stop, Target ===
if trade_direction == 'BUY':
    entry = low
    stop = high
    target = entry + 2 * (entry - stop)
else:
    entry = low
    stop = high
    target = entry - 2 * (stop - entry)

print(f"Trade Direction: {trade_direction}")
print(f"Entry: {entry}, Stop Loss: {stop}, Target: {target}")

# === Place Bracket Order ===
quantity = 10
bracket = ib.bracketOrder(
    action=trade_direction,
    totalQuantity=quantity,
    limitPrice=entry,
    takeProfitPrice=target,
    stopLossPrice=stop
)

for o in bracket:
    ib.placeOrder(contract, o)

print("Bracket order placed successfully.")
ib.disconnect()
