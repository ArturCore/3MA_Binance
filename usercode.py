from binance.client import Client
import numpy as np
import pandas as pd
import datetime

# Запускаємо стратегію
def handle(data):
    data = main(data)
    return data

# Функція для отримання поточних Klines (свічок)
def get_klines(client, symbol, interval, limit):
    klines = client.futures_klines(symbol=symbol, 
                                   interval=interval,
                                   limit=limit)
    return klines


def numpy_ewma_vectorized_v2(data, window):

    alpha = 2 /(window + 1.0)
    alpha_rev = 1-alpha
    n = data.shape[0]

    pows = alpha_rev**(np.arange(n+1))

    scale_arr = 1/pows[:-1]
    offset = data[0]*pows[1:]
    pw0 = alpha*alpha_rev**(n-1)

    mult = data*pw0*scale_arr
    cumsums = mult.cumsum()
    out = offset + cumsums*scale_arr[::-1]
    return out

def get_macd_info(data, short_period, long_period, signal_period):
#     data['ema_12'] = data["Close"].ewm(span=12, adjust=False, min_periods=12).mean() 
    ema_12 = numpy_ewma_vectorized_v2(data, short_period)
#     data['ema_26'] = data["Close"].ewm(span=26, adjust=False, min_periods=26).mean()
    ema_26 = numpy_ewma_vectorized_v2(data, long_period)
#     data['macd'] = data['ema_12'] - data['ema_26']
    macd = ema_12 - ema_26

    # Also we need "signal" line for comparing it to MACD. 
    # "signal" line is EMA(9) from MACD value
#     data['signal'] = data["macd"].ewm(span=9, adjust=False, min_periods=9).mean()
    signal = numpy_ewma_vectorized_v2(macd, signal_period)
    return macd.round(4), signal.round(4)

def calc_rsi(prices, period):
    prices_shift = np.roll(prices, 1)
    prices_shift[0] = np.nan
    pchg = (prices - prices_shift) / prices_shift
    
    alpha = 1 / period
    gain = np.where(pchg > 0, pchg, 0)
    avg_gain = np.full_like(gain, np.nan)
    
    loss = np.where(pchg < 0, abs(pchg), 0)
    avg_loss = np.full_like(loss, np.nan)
    
    avg_gain[period] = gain[1 : period + 1].mean()
    avg_loss[period] = loss[1 : period + 1].mean()
    
    for i in range(period + 1, gain.size):
        avg_gain[i] = alpha * gain[i] + (1 - alpha) * avg_gain[i - 1]
        avg_loss[i] = alpha * loss[i] + (1 - alpha) * avg_loss[i - 1]
        
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.round(4)


# Головна функція для стратегії
def main(data):
    try:
        # Connection to binance
        if data['environment'] == 'Production':
            client = Client(data['api_key'], data['api_secret'], testnet=False)
        else:
            client = Client(data['api_key'], data['api_secret'], testnet=True)
        result = {}

        # Get last data from binance about price for short period
        klines_short = get_klines(client, data['symbol'], data['short_interval'], data['limit'])  
        last_price = round(float(klines_short[-1][4]), 4)
        klines_short = klines_short[:-1]
        close_short = np.array([float(kline[4]) for kline in klines_short])
        # df_short = pd.DataFrame({'close': [float(kline[4]) for kline in klines_short],
        #                    'close_time': [kline[6] for kline in klines_short]})
        # df_short['close_time'] = pd.to_datetime(df_short['close_time'], unit='ms')
        # print(df_short)

        # Get last data from binance about price for long period
        klines_long = get_klines(client, data['symbol'], data['long_interval'], data['limit'])
        klines_long = klines_long[:-1]
        close_long = np.array([float(kline[4]) for kline in klines_long])
        # df_long = pd.DataFrame({'close': [float(kline[4]) for kline in klines_long],
        #                          'close_time': [kline[6] for kline in klines_long]})
        # df_long['close_time'] = pd.to_datetime(df_long['close_time'], unit='ms')
        # print(df_long)
        
        klines_trend = get_klines(client, data['symbol'], data['trend_interval'], data['limit'])  
        klines_trend = klines_trend[:-1]
        close_trend = np.array([float(kline[4]) for kline in klines_trend])
        # df_trend = pd.DataFrame({'close': [float(kline[4]) for kline in klines_trend],
        #                          'close_time': [kline[6] for kline in klines_trend]})
        # df_trend['close_time'] = pd.to_datetime(df_trend['close_time'], unit='ms')
        # print(df_trend)

        # MACD calculation
        macd_short, signal_short = get_macd_info(close_short, data['macd_short_period'], data['macd_long_period'], data['signal_period'])
        result['macd_short(-1)'] = macd_short[-1]
        result['macd_short(-2)'] = macd_short[-2]
        result['signal_short(-1)'] = signal_short[-1]
        result['signal_short(-2)'] = signal_short[-2]
        # print('short:', macd_short[-1], signal_short[-1])

        macd_long, signal_long = get_macd_info(close_long, data['macd_short_period'], data['macd_long_period'], data['signal_period'])
        result['macd_long(-1)'] = macd_long[-1]
        result['signal_long(-1)'] = signal_long[-1]
        # print('long:', macd_long[-1], signal_long[-1])

        macd_trend, signal_trend = get_macd_info(close_trend, data['macd_short_period'], data['macd_long_period'], data['signal_period'])
        result['macd_trend(-1)'] = macd_trend[-1]
        result['macd_trend(-2)'] = macd_trend[-2]
        result['macd_trend(-3)'] = macd_trend[-3]
        result['macd_trend(-4)'] = macd_trend[-4]
        result['macd_trend(-5)'] = macd_trend[-5]
        result['signal_trend(-1)'] = signal_trend[-1]
        result['signal_trend(-2)'] = signal_trend[-2]
        result['signal_trend(-3)'] = signal_trend[-3]
        result['signal_trend(-4)'] = signal_trend[-4]
        result['signal_trend(-5)'] = signal_trend[-5]
        # print('trend:', macd_trend[-1], signal_trend[-1])

        # RSI calculation
        rsi_short = calc_rsi(close_short, data['rsi_window'])
        result['rsi_short(-1)'] = rsi_short[-1]
        # print('rsi', rsi_short[-1])

        # Save dates which used in calculations for debugging
        date_format = '%Y-%m-%d %H:%M:%S'
        result['close_date(-1)'] = pd.to_datetime(klines_short[-1][6], unit='ms').strftime(date_format)
        result['close_date(-2)'] = pd.to_datetime(klines_short[-2][6], unit='ms').strftime(date_format)

        # Save last price
        result['last_close_price'] = last_price
        result['last_short_close_price'] = close_short[-1]

        data['result'] = result
        return data

    except Exception as e:
        data['result'] = str(e)
        return data



# BUYING LOGIC
# buy_first_cond = ((res['result']['macd_short(-2)'] < res['result']['signal_short(-2)']) and
#     (res['result']['macd_short(-1)'] > res['result']['signal_short(-2)']))
# buy_second_cond = (res['result']['macd_long(-1)'] < res['result']['macd_short(-1)'])
# buy_third_cond = (
#     ((res['result']['macd_trend(-1)'] - res['result']['signal_trend(-1)'])\
#      + (res['result']['macd_trend(-2)'] - res['result']['signal_trend(-2)'])
#      + (res['result']['macd_trend(-3)'] - res['result']['signal_trend(-3)'])
#     ) / 3 > 0
# )

# sell_first_cond = ((res['result']['macd_short(-2)'] > res['result']['signal_short(-2)']) and
#     (res['result']['macd_short(-1)'] < res['result']['signal_short(-2)']))
# sell_second_cond = (res['result']['signal_short(-1)'] > res['result']['macd_long(-1)'])
# sell_third_cond = (
#     ((res['result']['macd_trend(-1)'] - res['result']['signal_trend(-1)'])\
#      + (res['result']['macd_trend(-2)'] - res['result']['signal_trend(-2)'])
#      + (res['result']['macd_trend(-3)'] - res['result']['signal_trend(-3)'])
#      + (res['result']['macd_trend(-4)'] - res['result']['signal_trend(-4)'])
#      + (res['result']['macd_trend(-5)'] - res['result']['signal_trend(-5)'])
#     ) / 3 > 0
# )

# if buy_first_cond and buy_second_cond and buy_third_cond:
#     print("buy")
# elif: sell_first_cond and sell_second_cond and sell_third_cond:
#     print('sell')
# else:
#     print('wait')