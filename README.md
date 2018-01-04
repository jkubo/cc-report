# Crypto PE Report
Crypto PE Report, short for Cryptocurrency Private Equity Report, is a very simple script to generate a report of the current equity value of your cryptocurrency funds.

This report fetches your coin balances in various exchanges and generates a report of your ROI and gains via coinmarketcap API. The code currently supports Bittrex, Binance, KuCoin, Steemit, and Coinbase.

## Requirements
`Python 3.6+`

## Steps
1. Set Up Python

  Note: `Python 2.7` is not supported since Steemit (@jaykubo) does not provide a `Python 2` library.

  > $ virtualenv -p python3 env

  > $ source env/bin/activate

  > (env) $ python -V

  > (env) $ pip install -r requirements.txt

2. Adjust API keys

  Generate your API keys from your exchanges. I recommend revoking permissions for withdrawal.

  > $ cp conf/secrets.ini.dist conf/secrets.ini

  > $ vim conf/secrets.ini

3. Adjust shares

  Edit `shares.csv` to adjust the amount of contribution to the fund.

  > $ vim data/shares.csv

4. Run

  For one time run, this would suffice.

  > (env) $ python bin/generate.py

  For streaming, you can run `watch`

  > (env) $ watch -n30 "python bin/generate.py"
