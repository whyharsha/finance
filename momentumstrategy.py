from secrets import IEX_CLOUD_API_TOKEN as iex_tkn
import pandas as pd
import requests
from statistics import mean
from scipy import stats
import math

stocks_file = 'sp_500_stocks.csv'
api_url = "https://sandbox.iexapis.com/stable/"

def get_info(symbol):
    endpt = f"stock/{symbol}/stats?token={iex_tkn}"
    response = requests.get(api_url+endpt).json()
    
    return response

def get_stocks_info(stocks):
    symbol_strings = []

    for chunk in list(chunks(stocks['Ticker'], 100)):
        symbol_strings.append(','.join(chunk))

    symbol_string = ''
    data = []

    for elem in symbol_strings:
        symbol_string = elem
        batch_endpt = f"stock/market/batch?symbols={symbol_string}&types=price,stats&token={iex_tkn}"
        response = requests.get(api_url+batch_endpt).json()

        for symbol in symbol_string.split(","):
            data.append(
                {
                    'ticker': symbol,
                    'price' : response[symbol]['price'],
                    'one year': response[symbol]['stats']['year1ChangePercent'],
                    'one year percentile': 'N/A',
                    'six mnth': response[symbol]['stats']['month6ChangePercent'],
                    'six mnth percentile': 'N/A',
                    'three mnth': response[symbol]['stats']['month3ChangePercent'],
                    'three mnth percentile': 'N/A',
                    'one mnth': response[symbol]['stats']['month1ChangePercent'],
                    'one mnth percentile': 'N/A',
                    'hqm score': 'N/A'
                }
            )
    
    return pd.DataFrame(data)

def hqm(df, portfolio_size):
    #Sort in place
    df.sort_values('one year', ascending = False, inplace = True)
    df.reset_index(drop = True, inplace = True)

    #Calculate the percentiles and hqm score for each row
    for index, row in df.iterrows():
        df.at[index, 'one year percentile'] = stats.percentileofscore(df['one year'], row['one year'])
        df.at[index, 'six mnth percentile'] = stats.percentileofscore(df['six mnth'], row['six mnth'])
        df.at[index, 'three mnth percentile'] = stats.percentileofscore(df['three mnth'], row['three mnth'])
        df.at[index, 'one mnth percentile'] = stats.percentileofscore(df['one mnth'], row['one mnth'])
        df.at[index, 'hqm score'] = mean([row['one year'], row['six mnth'], row['three mnth'], row['one mnth']])

    #create a copy with just the cols we need, sort by hqm and keep the top 50
    df_hqm = df[['ticker', 'price', 'hqm score']].copy()
    df_hqm.sort_values('hqm score', ascending = True, inplace = True)
    df_hqm = df_hqm[:50]
    df_hqm.reset_index(drop = True, inplace = True)

    df_hqm['buy'] = 0
    
    #Calculate the number of shares to buy - in equal proportion
    position_size = portfolio_size / len(df_hqm)

    for index, row in df_hqm.iterrows():
        if row['price'] == 0:
            print(row['ticker'])
        else:
            df_hqm.at[index, 'buy'] = math.floor(position_size / row['price'])

    return df_hqm

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

def process_stocks():
    stocks = get_stocks(stocks_file)
    portfolio_size = portfolio_input()
    df = get_stocks_info(stocks)
    df_hqm = hqm(df, portfolio_size)
    df_hqm.to_csv('buy_momentum_stocks.csv', index = False)

if __name__ == "__main__":
    process_stocks()