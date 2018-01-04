import os
import json
import requests
from configparser import SafeConfigParser
import pandas as pd
import numpy as np
from coinbase.wallet.client import Client as Coinbase
from bittrex.bittrex import Bittrex, API_V2_0
from binance.client import Client as Binance
from kucoin.client import Client as KuCoin
from steem import Steem
from steem.converter import Converter

cfg = SafeConfigParser()
cfg.read('conf/secrets.ini')

# Exchanges
data = dict({
    'coinbase': {
        'client': Coinbase(
            api_key=cfg.get('Coinbase', 'api_key'),
            api_secret=cfg.get('Coinbase', 'api_secret')
        ),
        'columns': ['currency', 'amount']
    },
    'bittrex': {
        'client': Bittrex(
            api_key=cfg.get('Bittrex', 'api_key'),
            api_secret=cfg.get('Bittrex', 'api_secret'),
            api_version=API_V2_0
        ),
        'columns': ['Currency', 'Balance']
    },
    'binance': {
        'client': Binance(
            api_key=cfg.get('Binance', 'api_key'),
            api_secret=cfg.get('Binance', 'api_secret')
        ),
        'columns': ['asset', 'free']
    },
    'kucoin': {
        'client': KuCoin(
            api_key=cfg.get('KuCoin', 'api_key'),
            api_secret=cfg.get('KuCoin', 'api_secret')
        ),
        'columns': ['coinType', 'balance']
    }
})

try:
    data['coinbase']['accounts'] = data['coinbase']['client'].get_accounts()
    data['coinbase']['balances'] = [a.balance for a in data['coinbase']['accounts'].data]
except:
    data['coinbase']['message'] = '[Coinbase] API Error: Cannot retrieve balances'
    pass

try:
    data['bittrex']['accounts'] = data['bittrex']['client'].get_balances()
    data['bittrex']['balances'] = [x['Balance'] for x in data['bittrex']['accounts']['result']]
except:
    data['bittrex']['message'] = '[Bittrex] API Error: Cannot retrieve balances'
    pass

try:
    data['binance']['accounts'] = data['binance']['client'].get_account()
    data['binance']['balances'] = data['binance']['accounts']['balances']
except:
    data['binance']['message'] = '[Binance] API Error: Cannot retrieve balances'
    pass

try:
    data['kucoin']['balances'] = data['kucoin']['client'].get_all_balances()
except:
    data['kucoin']['message'] = '[KuCoin] API Error: Cannot retrieve balances'
    pass

# Steemit
client = Steem()
converter = Converter()
try:
    account = client.get_account(cfg.get('Steemit', 'user_account'))
    balance = converter.vests_to_sp(np.float(account['vesting_shares'].split()[0]))
except:
    pass

# Portfolio
def normalize(datum):
    try:
        df = pd.DataFrame(datum['balances']).filter(datum['columns'])
        df.columns = ['currency', 'balance']
        df['currency'] = df['currency'].apply(np.str)
        df['balance'] = df['balance'].apply(np.float)
    except:
        df = pd.DataFrame()
        pass
    return df

df = pd.concat(list(map(normalize, data.values())) + [
    normalize({'balances': [{'c': 'STEEM', 'b': balance}], 'columns': ['c', 'b']})
]).reset_index(drop=True)
portfolio = df[df['balance'].apply(abs) >= 0.001].groupby('currency', as_index=False).agg({
    'balance': np.sum
})

# Prices
ccm_api_url = 'https://api.coinmarketcap.com/v1/ticker'
ccm_api_res = requests.get(ccm_api_url, params={'limit': 5000})
prices = pd.DataFrame(json.loads(ccm_api_res.content))

# Reporting
summary = pd.merge(portfolio, prices, left_on='currency', right_on='symbol')
summary['usd'] = summary['balance'] * summary['price_usd'].apply(np.float)
summary['hourly'] = summary['usd'] - summary['usd'] / (1 + summary['percent_change_1h'].dropna().apply(np.float) / 100)
summary['daily'] = summary['usd'] - summary['usd'] / (1 + summary['percent_change_24h'].fillna(summary['percent_change_1h']).apply(np.float) / 100)
summary['weekly'] = summary['usd'] - summary['usd'] / (1 + summary['percent_change_7d'].fillna(summary['percent_change_24h']).apply(np.float) / 100)

# Holdings
shares = pd.read_csv('data/shares.csv')
total_value = sum(summary['usd'])
shares['shares'] = shares['shares'].apply(np.float)
shares['investment'] = shares['investment'].apply(np.float)
shares['percentage'] = shares['shares'] / sum(shares['shares'])
shares['value'] = shares['percentage'] * total_value
shares['gain_usd'] = shares['value'] - shares['investment']
shares['gain_ratio'] = shares['gain_usd'] / shares['investment']

print('=' * 80)
print(summary.filter([
    'symbol', 'balance', 'usd', 'hourly', 'daily', 'weekly'
]).sort_values('usd', ascending=False).reset_index(drop=True))

print('=' * 80)
hourly_gains = sum(summary['hourly'])
daily_gains = sum(summary['daily'])
weekly_gains = sum(summary['weekly'])
print('Hourly Gains:\t$ %.2f (%.2f %%)' % (hourly_gains, 100 * hourly_gains / (total_value - hourly_gains)))
print('Daily Gains:\t$ %.2f (%.2f %%)' % (daily_gains, 100 * daily_gains / (total_value - daily_gains)))
print('Weekly Gains:\t$ %.2f (%.2f %%)' % (weekly_gains, 100 * weekly_gains / (total_value - weekly_gains)))

print('=' * 80)
print(shares[['holder', 'shares', 'investment', 'value', 'gain_usd', 'gain_ratio']])

print('=' * 80)
print('Total Value:\t$ %.2f' % total_value)

print('=' * 80)
for key in data:
    if data[key].get('message'):
        print(data[key]['message'])
