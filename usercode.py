from binance.client import Client
import numpy as np
import pandas as pd

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

# Функція для обчислення середньої лінії (MA)
def calculate_ma(closing_prices, period):
    ma = np.convolve(closing_prices, np.ones(period)/period, mode='valid')
    return ma

# Допоміжна функція для розрахунку RSI
def rma(x, n):
    """Running moving average"""
    a = np.full_like(x, np.nan)
    a[n] = x[1:n+1].mean()
    for i in range(n+1, len(x)):
        a[i] = (a[i-1] * (n - 1) + x[i]) / n
    return a

# Головна функція для стратегії
def main(data):
    try:
        # Connection to binance
        if data['environment'] == 'Production':
            client = Client(data['api_key'], data['api_secret'])
        else:
            client = Client(data['api_key'], data['api_secret'], testnet=True)
        
        result = {}
        
        # Get last data from binance about price
        klines = get_klines(client, data['symbol'], data['interval'], data['limit'])
        df = pd.DataFrame({'close': [float(kline[4]) for kline in klines],
                           'close_time': [kline[6] for kline in klines]})
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')

        # MACD calculation
        df['ema_fast'] = df["close"].ewm(span=data['short_period'], adjust=False, min_periods=data['short_period']).mean() 
        df['ema_long'] = df["close"].ewm(span=data['long_period'], adjust=False, min_periods=data['long_period']).mean()
        df['macd'] = df['ema_fast'] - df['ema_long']
        df['signal'] = df["macd"].ewm(span=data['signal_period'], adjust=False).mean()

        # RSI calculation
        df['change'] = df['close'].diff()
        df['gain'] = df.change.mask(df.change < 0, 0.0)
        df['loss'] = -df.change.mask(df.change > 0, -0.0)
        df['avg_gain'] = rma(df.gain.to_numpy(), data['window'])
        df['avg_loss'] = rma(df.loss.to_numpy(), data['window'])
        df['rs'] = df.avg_gain / df.avg_loss
        df['rsi'] = 100 - (100 / (1 + df.rs))

        # Indeces of values for further calculations
        prev_index = -3
        last_index = -2

        # Save MACD indicators for further applying in logic
        result['prev_macd'] = df['macd'].iloc[prev_index].round(4)
        result['last_macd'] = df['macd'].iloc[last_index].round(4)
        result['prev_signal'] = df['signal'].iloc[prev_index].round(4)
        result['last_signal'] = df['signal'].iloc[last_index].round(4)

        # Calculate MACD crossover angle for further applying in logic
        step_back = 2
        x = [i for i in range(step_back)]
        y_signal = df['signal'].iloc[prev_index:last_index+1].values
        y_macd = df['macd'].iloc[prev_index:last_index+1].values
        slope_macd, intercept_macd = np.linalg.lstsq(np.vstack([x, np.ones(len(x))]).T, 
                                               y_macd,
                                               rcond=None)[0]
        slope_signal, intercept_signal = np.linalg.lstsq(np.vstack([x, np.ones(len(x))]).T, 
                                                   y_signal,
                                                   rcond=None)[0]
        tg_of_angle = abs((slope_signal-slope_macd) / (1 + slope_signal*slope_macd))
        result['calculated_angle'] = round(np.arctan(tg_of_angle) * 180 / np.pi, 4)

        # Save RSI indicators for further applying in logic
        result['prev_rsi'] = df['rsi'].iloc[prev_index].round(4)
        result['last_rsi'] = df['rsi'].iloc[last_index].round(4)

        # Save dates which used in calculations for debugging
        date_format = '%Y-%m-%d %H:%M:%S'
        result['prev_close_date'] = df['close_time'].iloc[prev_index].strftime(date_format)
        result['last_close_date'] = df['close_time'].iloc[last_index].strftime(date_format)

        # Save last price
        result['last_price'] = df['close'].iloc[-1]

        data['result'] = result
        return data

    except Exception as e:
        data['result'] = str(e)
        return data


# PARAMETERS
# data['api_key'] = 
# data['api_secret'] = 
# data['symbol'] = "BTCUSDT";
# data['interval'] = "5m"
# data['limit'] = 100
# data['position_size'] = 0.004
# # Mean strategy
# data['short_period'] = 10;
# data['long_period'] = 50;
# # RSI Strategy 
# data['window'] = 14
# data['upper_bound'] = 70
# data['lower_bound'] = 20
# # MACD Strategy 
# data['short_period'] = 12
# data['long_period'] = 26
# data['signal_period'] = 9
# data['angle'] = 1


# BUYING LOGIC
# if res['prev_macd'] < res['prev_signal'] and res['last_macd'] > res['last_signal']:
#     if res['angle'] > calculated_angle:
#         if res['last_rsi'] > res['upper_bound']: 
#             buy(res['position_size']) # купуємо на визначену кількість
# elif res['prev_signal'] < res['prev_macd'] and res['last_signal'] > res['last_macd']:
#     position.close() # Закриваємо позицію
