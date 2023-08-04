import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange



# Calculate Bollinger Bands and target variable
def prepare_data(symbol, start_date, end_date, dte):
    vix = yf.download('^VIX', start=start_date, end=end_date)
    data = yf.download(symbol, start=start_date, end=end_date)
    data['RollingStd'] = data['Adj Close'].rolling(window=20).std()
    data['VIX'] = vix['Adj Close']
    data['VIXRollingStd'] = data['VIX'].rolling(window=20).std()
    data['RSI'] = RSIIndicator(data['Adj Close'], window=14).rsi()
    data['ATR'] = AverageTrueRange(data['High'], data['Low'], data['Adj Close'], window=14).average_true_range()

    data['Target'] = data['RollingStd'].shift(-dte)
    data.dropna(inplace=True)

    features = data[['High', 'Low', 'Adj Close', 'Volume', 'RollingStd', 'VIX', 'VIXRollingStd', 'RSI', 'ATR']]
    target = data['Target']

    return features, target

def train_regression_model(fea