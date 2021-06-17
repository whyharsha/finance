import pandas as pd
import numpy as np
import xlsxwriter as xl
import requests
import math

stocks_file = "sp_500_stocks.csv"

def get_stocks(filename):
    stocks = pd.read_csv(filename)
    return stocks

def get_auth_key(username):
    