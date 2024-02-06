import ccxt
import pandas as pd
pd.set_option("display.max_rows", None)
from ta import momentum as mom
import time
import schedule
import warnings
warnings.filterwarnings('ignore')
# Define your API keys and other parameters
api_key = 'api_key'
api_secret = 'api_secret'
exchange_name = 'mexc'  # Replace with your exchange of choice
symbol = 'BTC/USDC'  # Replace with the trading pair you want to trade
target_asset = 'BTC'
risk_percent = 0.01  # 1% risk per trade
min_rr_ratio = 3
initial_balance = 10  # Replace with your desired initial capital
timeframe = '15m'

# Create an instance of the exchange
exchange = getattr(ccxt, exchange_name)({
 
    'apiKey': api_key,
    'secret': api_secret,
})
#list = exchange.fetch_markets()
#for market in list:
#    print(market)
balances = exchange.fetch_balance()
availableUsdt = balances['total']['USDC']

ob = exchange.fetch_order_book(symbol)
try:
    in_position = False
    def checkBuySellOrder(df):
        global in_position
        last_row_index = len(df.index) - 1
        spending = (availableUsdt * 0.8) / df['close'][last_row_index]
        if df['BullishDiv'][last_row_index]:
            if not in_position:
                try:
                    print('Buying...')
                    order = exchange.create_limit_buy_order(symbol, spending, ob['asks'][0][0])
                    print(order)
                    in_position = True
                except Exception as e:
                    print(e)
        if df['BearishDiv'][last_row_index]:
            if in_position:
                try:
                    print("Selling...")
                    bal = exchange.fetch_balance()['info']['balances']
                    free_balance = None
                    for item in bal:
                        if item['asset'] == target_asset:
                            free_balance = item['free']
                            break
                    order = exchange.create_limit_sell_order(symbol, free_balance, ob['bids'][0][0])
                    print(order)
                    in_position = False
                except Exception as e:
                    print(e)
    oversoldLevel   = 30
    overboughtLevel = 70
    def isBullishDivergence(close, low, low2, rsiVal):
        bullish_divergence = []
        for i in range(len(close)):
            if i == 0:
                bullish_divergence.append(False)
            else:
                if close[i] > low[i] and low2[i] > low[i] and rsiVal[i] < oversoldLevel and rsiVal[i-1] >= oversoldLevel:
                    bullish_divergence.append(True)
                else:
                    bullish_divergence.append(False)
        return bullish_divergence

    def isBearishDivergence(close, high, high2, rsiVal):
        bearish_divergence = []
        for i in range(len(close)):
            if i == 0:
                bearish_divergence.append(False)
            else:
                if close[i] < high[i] and high2[i] < high[i] and rsiVal[i] > overboughtLevel and rsiVal[i-1] <= overboughtLevel:
                    bearish_divergence.append(True)
                else:
                    bearish_divergence.append(False)
        return bearish_divergence
    def fetching():
        bars = exchange.fetch_ohlcv(symbol, timeframe, limit=400)
        df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['rsi'] = mom.rsi(df['close'])
        df['previous_low'] = df['low'].shift(1)
        df['previous_high'] = df['high'].shift(1)
        df['BullishDiv'] = isBullishDivergence(df['close'], df['low'], df['previous_low'], df['rsi'])
        df['BearishDiv'] = isBearishDivergence(df['close'], df['high'], df['previous_high'], df['rsi'])
        print(df.tail(5))
        checkBuySellOrder(df);
    schedule.every(10).seconds.do(fetching)
    while True:
        schedule.run_pending()
        time.sleep(1)
except Exception as e:
    print(e)
