# StockMarketAnalyzerimport streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import ta
import io
from datetime import datetime

st.set_page_config(page_title="📈 Stock Market Visualizer", layout="wide")

# Sidebar – Input section
st.sidebar.title("Stock Selection")
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL)", "AAPL")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2022-01-01"))
end_date = st.sidebar.date_input("End Date", datetime.today())

# Timeframe for chart
interval = st.sidebar.selectbox("Interval", ["1d", "1h", "15m"])

# Indicators
show_ma = st.sidebar.checkbox("Show Moving Averages")
show_rsi = st.sidebar.checkbox("Show RSI")
show_boll = st.sidebar.checkbox("Show Bollinger Bands")

# Fetch Data
@st.cache_data
def load_data(ticker, start, end, interval):
    data = yf.download(ticker, start=start, end=end, interval=interval)
    data.dropna(inplace=True)
    return data

df = load_data(ticker, start_date, end_date, interval)

st.title("📊 Stock Market Visualizer")
st.subheader(f"Showing data for {ticker.upper()}")

# Indicators
if show_ma:
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA50"] = df["Close"].rolling(window=50).mean()

if show_boll:
    bb = ta.volatility.BollingerBands(df["Close"])
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()

# Candlestick Chart
fig = go.Figure()

fig.add_trace(go.Candlestick(x=df.index,
                             open=df['Open'],
                             high=df['High'],
                             low=df['Low'],
                             close=df['Close'],
                             name="Candlesticks"))

if show_ma:
    fig.add_trace(go.Scatter(x=df.index, y=df["MA20"], name="MA 20", line=dict(width=1)))
    fig.add_trace(go.Scatter(x=df.index, y=df["MA50"], name="MA 50", line=dict(width=1)))

if show_boll:
    fig.add_trace(go.Scatter(x=df.index, y=df["bb_upper"], name="Boll Upper", line=dict(width=1)))
    fig.add_trace(go.Scatter(x=df.index, y=df["bb_lower"], name="Boll Lower", line=dict(width=1)))

fig.update_layout(title=f"{ticker.upper()} Price Chart", xaxis_rangeslider_visible=False)

st.plotly_chart(fig, use_container_width=True)

# RSI Chart
if show_rsi:
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
    rsi_fig = go.Figure()
    rsi_fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI"))
    rsi_fig.add_hline(y=70, line_dash="dash", line_color="red")
    rsi_fig.add_hline(y=30, line_dash="dash", line_color="green")
    rsi_fig.update_layout(title="Relative Strength Index", height=300)
    st.plotly_chart(rsi_fig, use_container_width=True)

# Export Chart
st.sidebar.markdown("### Export Chart")
export_format = st.sidebar.selectbox("Export format", ["PNG", "HTML"])
if st.sidebar.button("Export"):
    if export_format == "HTML":
        buffer = io.StringIO()
        fig.write_html(buffer)
        st.download_button("Download HTML", buffer.getvalue(), file_name=f"{ticker}_chart.html")
    elif export_format == "PNG":
        fig.write_image("temp.png")
        with open("temp.png", "rb") as f:
            st.download_button("Download PNG", f, file_name=f"{ticker}_chart.png")

# Portfolio Upload
st.sidebar.markdown("### Upload Portfolio CSV or Excel")
portfolio_file = st.sidebar.file_uploader("Upload file", type=["csv", "xlsx"])

if portfolio_file:
    try:
        if portfolio_file.name.endswith(".csv"):
            portfolio_df = pd.read_csv(portfolio_file)
        else:
            portfolio_df = pd.read_excel(portfolio_file)
        st.subheader("📁 Portfolio Data")
        st.dataframe(portfolio_df)

        tickers = portfolio_df["Ticker"].unique()
        st.write(f"Detected {len(tickers)} unique tickers.")
    except Exception as e:
        st.error(f"Could not load portfolio: {e}")

# Save configuration
st.sidebar.markdown("### Save/Load Configuration")
save_config = st.sidebar.button("📥 Save Config")
load_config = st.sidebar.file_uploader("📤 Load Config", type=["json"])

if save_config:
    config = {
        "ticker": ticker,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "interval": interval,
        "show_ma": show_ma,
        "show_rsi": show_rsi,
        "show_boll": show_boll
    }
    st.download_button("Download Config", data=pd.Series(config).to_json(), file_name="config.json")

if load_config:
    try:
        config_df = pd.read_json(load_config)
        st.success("Configuration loaded (refresh to apply changes).")
        st.json(config_df.to_dict())
    except Exception as e:
        st.error(f"Failed to load configuration: {e}")
