from binance.client import Client
import numpy as np

# Запускаємо стратегію
def handle(data):
    data["Result"] = main(data["api_key"], data["api_secret"], data["symbol"], data["short_period"], data["long_period"])
    return data

# Функція для отримання поточних Klines (свічок)
def get_klines(client, symbol):
    klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1HOUR)
    return klines

# Функція для обчислення середньої лінії (MA)
def calculate_ma(closing_prices, period):
    ma = np.convolve(closing_prices, np.ones(period)/period, mode='valid')
    return ma

# Головна функція для стратегії
def main(api_key, api_secret, symbol, short_period, long_period):
    try:
        client = Client(api_key, api_secret, testnet=True)

        klines = get_klines(client, symbol)
        closing_prices = np.array([float(kline[4]) for kline in klines])  # Закриття свічки

        short_ma = calculate_ma(closing_prices, short_period)
        long_ma = calculate_ma(closing_prices, long_period)

        last_short_ma = short_ma[-1]
        last_long_ma = long_ma[-1]

        if last_short_ma > last_long_ma:
            return 'Сигнал на покупку'
            # Тут можна виконати операції на покупку, використовуючи Binance API
        else:
            return 'Сигнал на продаж'
            # Тут можна виконати операції на продаж, використовуючи Binance API

    except Exception as e:
        print('Помилка:', e)
