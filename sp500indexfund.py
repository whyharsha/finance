import pandas as pd
import numpy as np
import xlsxwriter as xl
import requests
import math
from secrets import IEX_CLOUD_API_TOKEN as iex_tkn

stocks_file = 'sp_500_stocks.csv'
api_url = "https://sandbox.iexapis.com/stable/"
portfolio_size = 100000

def get_stocks(filename):
    stocks = pd.read_csv(filename)
    return stocks

#If you want individual stock info
def get_stock_info(symbol):
    quote_endpt = f"stock/{symbol}/quote?token={iex_tkn}"
    response = requests.get(api_url+quote_endpt).json()
    return {
        'ticker': symbol,
        'price': response['latestPrice'],
        'marketcap': response['marketCap'],
        'numbertobuy': 0
    }

#If you want to batch your request
def get_stocks_info(stocks):
    symbol_strings = []

    for chunk in list(chunks(stocks['Ticker'], 100)):
        symbol_strings.append(','.join(chunk))

    symbol_string = ''
    data = []

    for elem in symbol_strings:
        symbol_string = elem
        batch_endpt = f"stock/market/batch?symbols={symbol_string}&types=quote&token={iex_tkn}"
        response = requests.get(api_url+batch_endpt).json()

        for symbol in symbol_string:
            data.append(
                {
                    'ticker': symbol,
                    'price': response[symbol]['quote']['latestPrice'],
                    'marketcap': response[symbol]['quote']['marketCap'],
                    'numbertobuy': 0
                }
            )
    
    return pd.DataFrame(data)

def calculate_weights(df):
    total_market = df['marketcap'].cumsum()

    for index, row in df.iterrows():
        df[index]['numbertobuy'] = math.floor(float(row['marketcap']/total_market) * portfolio_size / row['price'])
    
    return df

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def process_stocks(stocks_file):
    stocks = get_stocks(stocks_file)
    df = get_stocks_info(stocks)
    df = calculate_weights(df)
    df.to_csv('buy_sp_500.csv', index = False)

if __name__ == "__main__":
    process_stocks(stocks_file)
