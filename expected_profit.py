from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import yoptions as yo
import yfinance as yf
import matplotlib.pyplot as plt
from scipy import stats
import argparse
from model_range_prediction import predict_std_in_days as fstd


class Strategy:
    def __init__(self, date, ticker, depth=1):
        risk_free_rate = yf.Ticker('^TNX').info['regularMarketOpen'] / 100
        self.dte = (datetime.strptime(date, '%Y-%m-%d') - datetime.today()).days + 1
        self.ticker = ticker
        self.calls = pd.DataFrame(yo.get_chain_greeks_date(stock_ticker=ticker, expiration_date=date, option_type='c', dividend_yield=0.0, risk_free_rate=risk_free_rate))
        self.puts = pd.DataFrame(yo.get_chain_greeks_date(stock_ticker=ticker, expiration_date=date, option_type='p', dividend_yield=0.0, risk_free_rate=risk_free_rate))
        self.stock_price = yo.get_underlying_price(self.calls['Symbol'][0])
        self.options = []
        self.depth = depth
        self.start_date = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=365 * depth)).strftime('%Y-%m-%d')
        self.exp_std = fstd(symbol= self.ticker, start_date=self.start_date, end_date=date, dte= self.dte)
        self.upper_price = self.stock_price + 2*self.exp_std
        self.lower_price = self.stock_price - 2*self.exp_std
        print("Upper Price:", self.upper_price)
        print("Lower Price:", self.lower_price)
        print("Calls on", date, ":\n", self.calls)
        print("Puts on", date, ":\n", self.puts)

    def add_option(self, option):
        self.options.append(option)

    def plot(self):
        S = self.stock_price

        # Range of stock for the profit graph
        stock_prices = np.arange(round(S * 0.8), round(S * 1.2), 0.1)

        # Initialize the combined profit to zero
        combined_profit = np.zeros_like(stock_prices)

        # Calculate the combined profit for all options
        for option in self.options:
            profits = option.get_profit(stock_prices)
            combined_profit += profits

        breakeven_price = round(stock_prices[np.argmin(np.abs(combined_profit))], 3)
        breakeven_profit = 0

        breakeven_index = np.abs(stock_prices - breakeven_price).argmin()

        profit_region = combined_profit >= 0
        loss_region = combined_profit < 0

        first_stdev_stock_prices = stock_prices[(stock_prices >= self.lower_price) & (stock_prices <= self.upper_price)]
        first_stdev_combined_profit = combined_profit[(stock_prices >= self.lower_price) & (stock_prices <= self.upper_price)]

        profit_integral = np.trapz(first_stdev_combined_profit[first_stdev_combined_profit >= 0], first_stdev_stock_prices[first_stdev_combined_profit >= 0])
        loss_integral = np.trapz(first_stdev_combined_profit[first_stdev_combined_profit < 0], first_stdev_stock_prices[first_stdev_combined_profit < 0])

        net_area = profit_integral + loss_integral

        print(f"Profit region area: {profit_integral.round(2)}")
        print(f"Loss region area: {loss_integral.round(2)}")

        print(f"Net area: {net_area.round(2)}")

        plt.figure(figsize=(8, 6))

        plt.fill_between(stock_prices, combined_profit, where=profit_region, color='green', alpha=0.5, label='Profit Region')
        plt.fill_between(stock_prices, combined_profit, where=loss_region, color='red', alpha=0.5, label='Loss Region')

        plt.plot(stock_prices, combined_profit, label=f'Combined Profit')
        plt.plot([self.lower_price, self.upper_price], [net_area, net_area], color='none', linestyle='--', lw=2, label=f'Expected Profit within 1 SD: {net_area.round(2)}')
        plt.axhline(y=0, color='gray', linestyle='--', lw=2)
        plt.axvline(x=self.upper_price, color='orange', linestyle='--', lw=2, label='Upper Price Range')
        plt.axvline(x=self.lower_price, color='orange', linestyle='--', lw=2, label='Lower Price Range')

        plt.scatter(x=breakeven_price, y=breakeven_profit, color='black', s=30, label=f'Breakeven Price: {breakeven_price}')

        for option in self.options:
            K = option.option['Strike']
            if option.call_or_put == 'c':
                plt.scatter(x=K, y=combined_profit[np.abs(stock_prices - K).argmin()], color='blue', s=30, label=f'Strike Price (Call Option {K})')
            elif option.call_or_put == 'p':
                plt.scatter(x=K, y=combined_profit[np.abs(stock_prices - K).argmin()], color='blue', s=30, label=f'Strike Price (Put Option {K})')

        plt.scatter(x=S, y=0, color='green', s=30, label=f'Current Stock Price: {S}')
        plt.xlabel('Stock Price')
        plt.ylabel('Profit/Loss')
        plt.title('Combined Option Profit/Loss')
        plt.legend()
        plt.grid(True)
        plt.show()

class Option:
    def __init__(self, option, direction, call_or_put):
        self.option = option
        self.direction = direction
        self.call_or_put = call_or_put

    def get_profit(self, stock_prices):
        P = self.option['Last Price']
        K = self.option['Strike']

        if self.call_or_put == 'c':
            profits = np.where(stock_prices > K, stock_prices - K, 0) - P
        elif self.call_or_put == 'p':
            profits = np.where(stock_prices < K, K - stock_prices, 0) - P
        else:
            raise ValueError("Invalid option type. Use 'c' for call options or 'p' for put options.")

        if self.direction == '-':
            profits = -profits

        return profits

def main():
    parser = argparse.ArgumentParser(description="Calculate and plot the combined profit/loss for options.")
    parser.add_argument("ticker", help="Stock ticker symbol")
    parser.add_argument("--exp_dates", action='store_true', help="Flag to get expiration dates of the options")
    parser.add_argument("date", nargs='?', default=None, help="Expiration date for the options (format: YYYY-MM-DD)")
    args = parser.parse_args()

    ticker = args.ticker

    if args.exp_dates: # If expiration dates are specified
        exp_dates = yo.get_expiration_dates(ticker)
        print(f"Expiration dates for {ticker}:")
        for date in exp_dates:
            print((datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')) #Days are off by 1 for some reason
        return
    
    date = args.date

    profit_calculator = Strategy(date=date, ticker=ticker, depth=1)

    print(f"Current {ticker} price: {profit_calculator.stock_price}")
    while True:
        command = input("Enter option command (<-|+><c|p> <strike_price>), or 'plot', 'reset', 'quit': ")
        if command == 'plot':
            profit_calculator.plot()
            continue
        if command == 'reset':
            profit_calculator = Strategy(date=date, ticker=ticker, depth=1)
            print("Selected options removed")
            print(f"Current {ticker} price: {profit_calculator.stock_price}")
            continue
        if command == 'quit ':
            break

        try:
            option_type, strike_price = command.split()
            strike_price = float(strike_price)  # Convert to float
            #Call option
            if option_type == "-c":
                option = Option(option=profit_calculator.calls[profit_calculator.calls['Strike'] == strike_price].iloc[0], direction='-', call_or_put='c')
            elif option_type == "+c":
                option = Option(option=profit_calculator.calls[profit_calculator.calls['Strike'] == strike_price].iloc[0], direction='+', call_or_put='c')
            #Put option
            elif option_type == "-p":
                option = Option(option=profit_calculator.puts[profit_calculator.puts['Strike'] == strike_price].iloc[0], direction='-', call_or_put='p')
            elif option_type == "+p":
                option = Option(option=profit_calculator.puts[profit_calculator.puts['Strike'] == strike_price].iloc[0], direction='+', call_or_put='p')
            else:
                raise ValueError("Invalid option type. Use '-c' for call options, '-p' for put options, or 'plot', 'reset, 'quit")
            profit_calculator.add_option(option)
        except (ValueError, IndexError) as e:
            print("Option not found, make sure the strike price is valid.")

if __name__ == "__main__":
    main()
