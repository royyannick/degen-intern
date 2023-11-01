import requests
import ast
import pandas as pd
from datetime import datetime, date, timedelta

import streamlit as st
from streamlit_lightweight_charts import renderLightweightCharts

# Mapping of token symbols to their full names
TOKEN_MAPPING = {
    "ETH": "Ethereum",
    "BTC": "Bitcoin",
    "SOL": "Solana",
    "AVAX": "Avalanche",
    "ADA": "Cardano",
    "XRP": "XRP"
}


def plot_chart(price_df):
    # https://tradingview.github.io/lightweight-charts/docs/api

    chartOptions = {
        "height": 400,
        "layout": {
            "textColor": 'black',
            "background": {
                "type": 'solid',
                "color": 'white'
            },
        },
        "timeScale": {
            #"borderColor": '#e2e5e8',
            "timeVisible": True,
        },
    }

    seriesCandlestickChart = [
        {
            "type": 'Candlestick',
            "data": price_df.to_dict(orient='records'),
            "options": {
                "upColor": '#26a69a',
                "downColor": '#ef5350',
                "borderVisible": False,
                "wickUpColor": '#26a69a',
                "wickDownColor": '#ef5350'
            }
        }
    ]

    renderLightweightCharts([
        {
            "chart": chartOptions,
            "series": seriesCandlestickChart
        }
    ], 'candlestick')


def fetch_prices(token, start_time, end_time=None):
    pair = token+'USDT'
    binance_url = "https://api.binance.com/api/v3/klines?symbol={}&interval=1h&startTime={}&limit=1000".format(
        pair, str(start_time*1000))
    print(binance_url)

    price_response = ast.literal_eval(requests.get(binance_url).text)
    price_df = pd.DataFrame(price_response, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'date', 'asset_vol', 'txs', 'irr', 'irr2', 'irr3'])
    price_df = price_df[['time', 'open', 'high', 'low', 'close', 'volume']]
    price_df['time'] = price_df['time'].apply(lambda x: int(x/1000))
    
    return price_df

st.set_page_config(layout="wide")
st.header("🦍 Degen Together Strong.")

# Sidebar with dropdown list
selected_crypto_fullname = st.sidebar.selectbox('Select Token:', list(TOKEN_MAPPING))
# Get the token symbol for the selected crypto
selected_token = [token for token, name in TOKEN_MAPPING.items() if token == selected_crypto_fullname][0]

# Date input fields for start and end date
start_date = st.sidebar.date_input('Start date', date.today() - timedelta(days=30))
end_date = st.sidebar.date_input('End date', date.today())

# Convert dates to timestamps
start_timestamp = int(start_date.strftime('%s'))
end_timestamp = int(end_date.strftime('%s'))

# Button to fetch prices
if st.sidebar.button('Fetch Prices'):
    # Call your fetch_prices function here
    price_df = fetch_prices(selected_token, start_timestamp, end_timestamp)

    plot_chart(price_df)
