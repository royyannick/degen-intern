import requests
import ast
import pandas as pd
from datetime import datetime, date, timedelta

import streamlit as st
from streamlit_lightweight_charts import renderLightweightCharts

# ==========================================================================================
# ==========================================================================================
# Constants
# ==========================================================================================
# Mapping of token symbols to their full names
TOKEN_MAPPING = {
    "ETH": "Ethereum",
    "BTC": "Bitcoin",
    "SOL": "Solana",
    "AVAX": "Avalanche",
    "ADA": "Cardano",
    "XRP": "XRP"
}

# Session state variables
if st.session_state.get('price_df') is None:
    st.session_state['price_df'] = pd.DataFrame()

if st.session_state.get('liquidation_price') is None:
    st.session_state['liquidation_price'] = 0

if st.session_state.get('date_range') is None:
    st.session_state['date_range'] = "custom"

# ==========================================================================================
# ==========================================================================================
# Utility Functions
# ==========================================================================================
def plot_chart(price_df, liquidation_price=None):
    # https://tradingview.github.io/lightweight-charts/docs/api

    chartOptions = {
        "height": 400,
        "layout": {
            "textColor": 'white',
            "background": {
                #"type": 'solid',
                "color": 'black'
            },
        },
        "timeScale": {
            #"borderColor": '#e2e5e8',
            "timeVisible": True,
        },
        "grid": {
            "vertLines": {
                "color": 'rgba(197, 203, 206, 0.5)', #// light grey color with reduced opacity
                "style": 1,  #"solid", #// or LightweightCharts.LineStyle.Solid
                "visible": True,
            },
            "horzLines": {
                "color": 'rgba(197, 203, 206, 0.5)',
                "style": 1,  #"solid", #// or LightweightCharts.LineStyle.Solid
                "visible": True,
            },
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
            },
            # "markers": [{
            #     "time": int(price_df.at[len(price_df)-20, 'time']),
            #     "position": 'aboveBar',
            #     "color": '#000',
            #     "shape": 'arrowUp',
            #     #"text": '1800 Resistance',
            #     "size": 1
            # }]
        },
    ]
    if liquidation_price is not None and liquidation_price > 0:
        seriesCandlestickChart.append(
            {
                "type": 'Line',
                "data": [{"time": int(price_df.at[0, 'time']), "value": liquidation_price}, {"time": int(price_df.at[len(price_df)-1, 'time']), "value": liquidation_price}],
                #"text": "1800 Resistance",
                "options": {
                    "lineWidth": 1,
                    "color": '#ef5350',
                },
                # https://tradingview.github.io/lightweight-charts/docs/api#seriesmarkershape
                # "circle" | "square" | "arrowUp" | "arrowDown"
                # "markers": [{
                #     "time": int(price_df.at[len(price_df)-1, 'time']),
                #     "position": 'aboveBar',
                #     "color": '#000',
                #     "shape": 'text',
                #     "text": '1800 Resistance',
                #     "size": 12
                # }]
            })
            # {
            #     "type": 'Marker',
            #     "time": int(price_df.at[20, 'time']),
            #     #position: 'aboveBar',
            #     "color": '#f68410',
            #     "shape": 'circle',
            #     "text": 'Mark Me!'
            # }

    renderLightweightCharts([
        {
            "chart": chartOptions,
            "series": seriesCandlestickChart
        }
    ], 'candlestick')


@st.cache_data
def fetch_prices(token, start_time, end_time=None, interval='1h', source='Binance'):
    if source == 'Binance':
        pair = token+'USDT'
        binance_url = "https://api.binance.us/api/v3/klines?symbol={}&interval={}&startTime={}&endTime={}&limit=1000".format(
            pair, interval, str(start_time*1000), str(end_time*1000))
        print(binance_url)
        st.write(binance_url)

        price_response = ast.literal_eval(requests.get(binance_url).text)
        price_df = pd.DataFrame(price_response, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'date', 'asset_vol', 'txs', 'irr', 'irr2', 'irr3'])
        price_df = price_df[['time', 'open', 'high', 'low', 'close', 'volume']]
        price_df['time'] = price_df['time'].apply(lambda x: int(x/1000))
    elif source == 'Coingecko':
        st.write('Working on it.')

    return price_df


def calculate_liquidation_price(entry_price, leverage, liquidation_limit=0.95, is_long=True):
    """
    Calculate the liquidation price for a long position based on entry price, leverage, and liquidation limit.

    :param entry_price: The entry price of the crypto asset.
    :param leverage: The leverage amount.
    :param liquidation_limit: The liquidation limit (default is 95%, represented as 0.95).
    :return: The liquidation price.
    """
    if leverage <= 1:
        return 0

    if is_long:
        # For a long position, the liquidation price is lower than the entry price.
        liquidation_price = entry_price * (1 - ((1 - liquidation_limit) / leverage))
    else:
        # For a short position, the liquidation price is higher than the entry price.
        liquidation_price = entry_price * (1 + ((1 - liquidation_limit) / leverage))

    return liquidation_price


# ==========================================================================================
# ==========================================================================================
# Streamlit App
# ==========================================================================================
st.set_page_config(layout="wide")
st.header("🦍 Degen Together Strong.")

st.sidebar.markdown('## Degen Config')

# Sidebar
prices_source = st.sidebar.radio('Prices Source:', ['Binance', 'Goingecko'], horizontal=True)

# Symbol selection
selected_crypto_fullname = st.sidebar.selectbox('Select Token:', list(TOKEN_MAPPING))
selected_token = [token for token, name in TOKEN_MAPPING.items() if token == selected_crypto_fullname][0]

# Interval selection
interval = st.sidebar.radio("Interval", ['5m', '1h', '4h', '1d', '1w', '1M'], key='Interval', horizontal=True)

side_date_col1, side_date_col2 = st.sidebar.columns([1,1])
if st.session_state['date_range'] == "custom":
    st.session_state['start_timestamp'] = datetime.now() - timedelta(days=30)
    st.session_state['end_timestamp'] = datetime.now()
elif st.session_state['date_range'] == "1D":
    st.session_state['start_timestamp'] = datetime.now() - timedelta(days=1)
    st.session_state['end_timestamp'] = datetime.now()
elif st.session_state['date_range'] == "1W":
    st.session_state['start_timestamp'] = datetime.now() - timedelta(days=7)
    st.session_state['end_timestamp'] = datetime.now()
elif st.session_state['date_range'] == "1M":
    st.session_state['start_timestamp'] = datetime.now() - timedelta(days=30)
    st.session_state['end_timestamp'] = datetime.now()
elif st.session_state['date_range'] == "1Y":
    st.session_state['start_timestamp'] = datetime.now() - timedelta(days=365)
    st.session_state['end_timestamp'] = datetime.now()

start_date = side_date_col1.date_input('Start date', st.session_state['start_timestamp']) #date.today() - timedelta(days=30))
end_date = side_date_col2.date_input('End date', st.session_state['end_timestamp']) #date.today())

start_timestamp = int(start_date.strftime('%s'))
end_timestamp = int(end_date.strftime('%s'))

# Buttons for last day, last week, last month, last year
side_button_col1, side_button_col2, side_button_col3, side_button_col4 = st.sidebar.columns([1,1,1,1])
if side_button_col1.button('1D', use_container_width=True):
    st.session_state['date_range'] = "1D"
    st.rerun()
if side_button_col2.button('1W', use_container_width=True):
    st.session_state['date_range'] = "1W"
    st.rerun()
if side_button_col3.button('1M', use_container_width=True):
    st.session_state['date_range'] = "1M"
    st.rerun()
if side_button_col4.button('1Y', use_container_width=True):
    st.session_state['date_range'] = "1Y"
    st.rerun()

if st.sidebar.button('Fetch Prices', use_container_width=True):
    try:
        st.write(f'Fetching prices with: {selected_token}, {start_timestamp}, {end_timestamp}, {interval}')
        # Fetch prices
        price_df = fetch_prices(selected_token, start_timestamp, end_timestamp, interval=interval)
        st.session_state['price_df'] = price_df
        st.write(price_df)
        if len(price_df) == 1000:
            st.sidebar.warning('1000 Limit Reached.')
            st.sidebar.warning('Dymanic pagination coming soon!')
    except Exception as e:
        st.sidebar.exception(e)

price_df = st.session_state['price_df']
if len(price_df) > 0:
    side_leverage_col1, side_leverage_col2 = st.sidebar.columns([1,1])
    if not side_leverage_col1.checkbox('Leverage'):
        # Plot chart
        plot_chart(price_df)
    else:
        liquidation_threshold = side_leverage_col2.text_input('Liq. Threshold (%)', value='95')
        # Slider for leverage selection
        leverage = st.sidebar.slider('Select your leverage:', min_value=1, max_value=50, value=10)
        is_long = st.sidebar.radio('Are you going long or short?', ['Long', 'Short']) == 'Long'
        liquidation_price = calculate_liquidation_price(float(price_df.iloc[-1]['close']), float(leverage), int(liquidation_threshold)/100, is_long=is_long)
        plot_chart(price_df, liquidation_price)
        #st.write(f'The liquidation price at {leverage}x leverage is: ${liquidation_price:.2f}')

# add todos to sidebar in expander.
st.sidebar.markdown('---')
expand_todo = st.sidebar.expander('Todos')
expand_todo.markdown('- [ ] Fetch pagination')
expand_todo.markdown('- [ ] Liquidation overlay')
expand_todo.markdown('- [ ] Supports')
expand_todo.markdown('- [ ] Resistances')
expand_todo.markdown('- [ ] Trends')
expand_todo.markdown('- [ ] Recommendations')
expand_todo.markdown('- [ ] Sweep Tokens')
expand_todo.markdown('- [ ] Report')
if expand_todo.button('Clear Cache 👍'):
    st.cache_data.clear()

st.sidebar.markdown('---')
st.sidebar.markdown('`May the gains be with you. 🚀 🌕`')