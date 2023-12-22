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

def train_regression_model(features_train, target_train):
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(features_train, target_train)
    return model

def evaluate_regression_model(model, features_test, target_test):
    predictions = model.predict(features_test)
    mse = mean_squared_error(target_test, predictions)
    rmse = np.sqrt(mse)
    print('Mean Squared Error: ', mse)
    print('Root Mean Squared Error: ', rmse)

def predict_std_in_days(symbol, start_date, end_date, dte):
    features, target = prepare_data(symbol, start_date, end_date, dte)
    features_train, features_test, target_train, target_test = train_test_split(features, target, test_size=0.2, random_state=42)
    model = train_regression_model(features_train, target_train)
    evaluate_regression_model(model, features_test, target_test)
    
    # Use the last instance in features_test to represent the point dte days ahead
    prediction = model.predict(features_test[-1:])
    print("Predicted price range within 1 stdev at expiration", prediction[0])  # Access the first element of the prediction array

    return prediction[0]



