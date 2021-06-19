from secrets import IEX_CLOUD_API_TOKEN as iex_tkn
import pandas as pd
import requests
from statistics import mean
from scipy import stats
import math

stocks_file = 'sp_500_stocks.csv'
api_url = "https://sandbox.iexapis.com/stable/"

def get_stocks_info(stocks):
    symbol_strings = []

    for chunk in list(chunks(stocks['Ticker'], 100)):
        symbol_strings.append(','.join(chunk))

    symbol_string = ''
    data = []

    for elem in symbol_strings:
        symbol_string = elem
        batch_endpt = f"stock/market/batch?symbols={symbol_string}&types=quote,advanced-stats&token={iex_tkn}"
        response = requests.get(api_url+batch_endpt).json()

        for symbol in symbol_string.split(","):
            ev = response[symbol]['advanced-stats']['enterpriseValue']
            ebitda = response[symbol]['advanced-stats']['EBITDA']
            gross_profit = response[symbol]['advanced-stats']['grossProfit']

            if not (ev == None or ebitda == None or gross_profit == None or ebitda == 0 or gross_profit == 0):
                data.append(
                    {
                        'ticker': symbol,
                        'price': response[symbol]['quote']['latestPrice'],
                        'ev': ev,
                        'EBITDA': ebitda,
                        'gross profit': gross_profit,
                        'price to earnings': response[symbol]['quote']['peRatio'],
                        'PE Percentile': 'N/A',
                        'price to book': response[symbol]['advanced-stats']['priceToBook'],
                        'PB Percentile': 'N/A',
                        'price to sales': response[symbol]['advanced-stats']['priceToSales'],
                        'PS Percentile': 'N/A',
                        'ev to ebitda': (ev/ebitda),
                        'EVEBITDA Percentile': 'N/A',
                        'ev to gross profit': (ev/gross_profit),
                        'EVGP Percentile': 'N/A',
                        'value score': 0
                    }
                )
    
    return pd.DataFrame(data)

def value(df, portfolio_size):
    #remove negative pe stocks, sort in ascending and take the top 50
    df = df[df['price to earnings'] > 0]
    df.sort_values('price to earnings', inplace = True)
    df.reset_index(drop = True, inplace = True)

    #filling in missing data
    df['price to earnings'].fillna(df['price to earnings'].mean(), inplace = True)
    df['price to book'].fillna(df['price to book'].mean(), inplace = True)
    df['price to sales'].fillna(df['price to sales'].mean(), inplace = True)

    #Calculate the percentiles and hqm score for each row
    for index, row in df.iterrows():
        df.at[index, 'PE Percentile'] = stats.percentileofscore(df['price to earnings'], row['price to earnings'])
        df.at[index, 'PB Percentile'] = stats.percentileofscore(df['price to book'], row['price to book'])
        df.at[index, 'PS Percentile'] = stats.percentileofscore(df['price to sales'], row['price to sales'])
        df.at[index, 'EVEBITDA Percentile'] = stats.percentileofscore(df['ev to ebitda'], row['ev to ebitda'])
        df.at[index, 'EVGP Percentile'] = stats.percentileofscore(df['ev to gross profit'], row['ev to gross profit'])

        vals = []
        vals.append(df.at[index, 'PE Percentile'])
        vals.append(df.at[index, 'PB Percentile'])
        vals.append(df.at[index, 'PS Percentile'])
        vals.append(df.at[index, 'EVEBITDA Percentile'])
        vals.append(df.at[index, 'EVGP Percentile'])

        df.at[index, 'value score'] = mean(vals)
    
    #create a copy with just the cols we need, sort by value score and keep the top 50
    df_value = df[['ticker', 'price', 'value score']].copy()
    df_value.sort_values('value score', ascending = False, inplace = True)
    df_value = df_value[:50]
    df_value.reset_index(drop = True, inplace = True)

    #Calculate the number of shares to buy - in equal proportion
    position_size = portfolio_size / len(df_value)

    for index, row in df_value.iterrows():
        if row['price'] == 0:
            print(row['ticker'])
        else:
            df_value.at[index, 'buy'] = math.floor(position_size / row['price'])

    return df_value

def portfolio_input():
    portfolio_size = input('Enter the size of your portfolio: ')

    while not (portfolio_size.isnumeric() or portfolio_size >= 1000000):
        portfolio_size = input('You can only use a number a million or greater. Enter the size of your portfolio: ')
    
    return float(portfolio_size)

def get_stocks(filename):
    stocks = pd.read_csv(filename)
    return stocks

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def process_stocks():
    stocks = get_stocks(stocks_file)
    portfolio_size = portfolio_input()
    df = get_stocks_info(stocks)
    df_value = value(df, portfolio_size)
    df_value.to_csv('buy_value_stocks.csv', index = False)

if __name__ == "__main__":
    process_stocks()