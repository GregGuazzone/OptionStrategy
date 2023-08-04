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
        self.dte = (datetime.strptime(date, '%Y-%m-%d') - datetime.today()).days + 1
        self.ticker = ticker
        self.calls = pd.DataFrame(yo.get_chain_greeks_date(stock_ticker=ticker, expiration_date=date, option_type='c', dividend_yield=0.0, risk_free_rate=0.0))
        self.puts = pd.DataFrame(yo.get_chain_greeks_date(stock_ticker=ticker, expiration_date=date, option_type='p', dividend_yield=0.0, risk_free_rate=0.0))
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

        # Find the breakeven point
        breakeven_price = round(stock_prices[np.argmin(np.abs(combined_profit))], 3)
        breakeven_profit = 0

        # Find the index of the breakeven_price in stock_prices
        breakeven_index = np.abs(stock_prices - breakeven_price).argmin()

        # Create profit and loss regions for fill_between
        profit_region = combined_profit >= 0
        loss_region = combined_profit < 0

        # Plot the combined profit graph
        plt.figure(figsize=(8, 6))

        # Plot profit and loss regions as filled surfaces
        plt.fill_between(stock_prices, combined_profit, where=profit_region, color='green', alpha=0.5, label='Profit Region')
        plt.fill_between(stock_prices, combined_profit, where=loss_region, color='red', alpha=0.5, label='Loss Region')

        plt.plot(stock_prices, combined_profit, label='Combined Profit')
        plt.axhline(y=0, color='gray', linestyle='--', lw=2)
        plt.axvline(x=self.upper_price, color='orange', linestyle='--', lw=2, label='Upper Price Range')
        plt.axvline(x=self.lower_price, color='orange', linestyle='--', lw=2, label='Lower Price Range')

        # Plot the breakeven point on the combined profit line
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
    parser.add_argument("date", help="Expiration date for the options (format: YYYY-MM-DD)")
    parser.add_argument("ticker", help="Stock ticker symbol")
    args = parser.parse_args()

    date = args.date
    ticker = args.ticker

    profit_calculator = Strategy(date=date, ticker=ticker, depth=1)

    while True:
        command = input("Enter option command (- c or - p, and the strike price) e.g: \"- c 100\", or 'q' to quit: ")
        if command == 'q':
            break

        try:
            direction, option_type, strike_price = command.split()
            strike_price = float(strike_price)  # Convert to float
            if option_type == "c":
                option = Option(option=profit_calculator.calls[profit_calculator.calls['Strike'] == strike_price].iloc[0], direction=direction, call_or_put='c')
            elif option_type == "p":
                option = Option(option=profit_calculator.puts[profit_calculator.puts['Strike'] == strike_price].iloc[0], direction=direction, call_or_put='p')
            else:
                raise ValueError("Invalid option type. Use '- c' for call options or '- p' for put options.")

            profit_calculator.add_option(option)
        except (ValueError, IndexError) as e:
            print("Invalid command. Please try again.")

    profit_calculator.plot()

if __name__ == "__main__":
    main()
