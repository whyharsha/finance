import pandas as pd
import requests
import math
from secrets import IEX_CLOUD_API_TOKEN as iex_tkn

stocks_file = 'sp_500_stocks.csv'
api_url = "https://sandbox.iexapis.com/stable/"



#If you want individual stock info
def get_stock_info(symbol):
    quote_endpt = f"stock/{symbol}/quote?token={iex_tkn}"
    response = requests.get(api_url+quote_endpt).json()
    return {
        'ticker': symbol,
        'price': response['latestPrice'],
        'marketcap': response['marketCap'],
        'buy': 0
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

        for symbol in symbol_string.split(","):
            data.append(
                {
                    'ticker': symbol,
                    'price': response[symbol]['quote']['latestPrice'],
                    'marketcap': response[symbol]['quote']['marketCap'],
                    'buy': 0
                }
            )
    
    return pd.DataFrame(data)

def calculate_weights(df, portfolio_size):
    total_market = df['marketcap'].sum()

    for index, row in df.iterrows():
        df.at[index, 'buy'] = math.floor(((row['marketcap']/total_market) * portfolio_size) / row['price'])
    
    return df

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def portfolio_input():
    portfolio_size = input('Enter the size of your portfolio: ')

    while not (portfolio_size.isnumeric() or portfolio_size >= 1000000):
        portfolio_size = input('You can only use a number a million or greater. Enter the size of your portfolio: ')
    
    return float(portfolio_size)

def get_stocks(filename):
    stocks = pd.read_csv(filename)
    return stocks

def process_stocks(stocks_file):
    stocks = get_stocks(stocks_file)
    portfolio_size = portfolio_input()
    df = get_stocks_info(stocks)
    df = calculate_weights(df, portfolio_size)
    df.to_csv('buy_sp_500.csv', index = False)

if __name__ == "__main__":
    process_stocks(stocks_file)
