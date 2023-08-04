## Table of Contents
- [Setup](#setup)
- [Usage](#usage)
    - [Usage Examples](#usage-examples)
        - [Adding Options to strategy](#add-options)
        - [Charting the profit graph](#profit-graph)
- [Planned Features](#planned-features)

## Setup

##### 1. Clone or download this repository to your local machine.

```bash
git clone https://github.com/GregGuazzone/Options-Expected-Profit.git
cd optionstrategy
```

##### 2. Create a virtual environment to isolate project dependencies (optional but recommended).

*macOS/Linux*
```bash
python3 -m venv venv
source venv/bin/activate
```

*Windows*
```bash
python -m venv venv
venv\Scripts\activate
```

##### 3. Install the required libraries from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

## Usage

#### Usage Examples

##### Get the Option Chain For a Specific Date
To get the available expiration dates for a specific stock, use the --exp_dates option:

```bash
python3 expected_profit.py <date> <ticker>
```
Example:
```bash
python3 expected_profit.py 2023-08-11 AAPL
```

##### Adding an option to the strategy
```bash
<+(buy), -(sell)> <c(call), p(put)> <strike>
```
Example:
```bash
- c 100
```

##### Charting the strategy
```bash
q
```

## Planned features
- Using the expected standard deviation and the amount of profit/loss in those areas, calculating the expected profit/loss this option strategy should generate. (Instead of just representing it)
- Combining options from multiple different days. (This currently only supports adding options all from one specific day)

## Contributing

If you find any issues or have suggestions for improvements especially on the model used to estimate the price range, feel free to open an issue or submit a pull request.