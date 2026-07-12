"""
Stock Market Dashboard
----------------------
An interactive stock market dashboard built with Streamlit, yfinance, and Plotly.

Run with:
    streamlit run app.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ----------------------------------------------------------------------------
# Page configuration
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------

@st.cache_data(ttl=300)  # cache for 5 minutes
def load_price_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Download historical OHLCV data for a ticker."""
    data = yf.Ticker(ticker).history(period=period, interval=interval)
    if not data.empty:
        data.index = data.index.tz_localize(None)
    return data


@st.cache_data(ttl=300)
def load_company_info(ticker: str) -> dict:
    """Fetch company/summary info for a ticker."""
    try:
        return yf.Ticker(ticker).info
    except Exception:
        return {}


def add_moving_averages(df: pd.DataFrame, windows=(20, 50)) -> pd.DataFrame:
    df = df.copy()
    for w in windows:
        df[f"SMA{w}"] = df["Close"].rolling(window=w).mean()
    return df


def compute_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def format_large_number(n):
    if n is None or n == "N/A":
        return "N/A"
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "N/A"
    for unit in ["", "K", "M", "B", "T"]:
        if abs(n) < 1000:
            return f"{n:,.2f}{unit}"
        n /= 1000
    return f"{n:,.2f}P"


# ----------------------------------------------------------------------------
# Sidebar controls
# ----------------------------------------------------------------------------
st.sidebar.title("📊 Dashboard Controls")

default_ticker = "AAPL"
ticker_input = st.sidebar.text_input("Primary ticker symbol", value=default_ticker).upper().strip()

period_options = {
    "5 Days": "5d",
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "Year to Date": "ytd",
    "1 Year": "1y",
    "2 Years": "2y",
    "5 Years": "5y",
    "Max": "max",
}
period_label = st.sidebar.selectbox("Time period", list(period_options.keys()), index=3)
period = period_options[period_label]

interval_options = {
    "5 Days": "15m",
    "1 Month": "1d",
    "3 Months": "1d",
    "6 Months": "1d",
    "Year to Date": "1d",
    "1 Year": "1d",
    "2 Years": "1wk",
    "5 Years": "1wk",
    "Max": "1mo",
}
interval = interval_options[period_label]

chart_type = st.sidebar.radio("Chart type", ["Candlestick", "Line"], index=0)

show_sma = st.sidebar.checkbox("Show moving averages (SMA 20 / 50)", value=True)
show_rsi = st.sidebar.checkbox("Show RSI (14)", value=True)
show_volume = st.sidebar.checkbox("Show volume", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("Compare with other tickers")
compare_input = st.sidebar.text_input(
    "Comma-separated tickers (optional)", value="MSFT, GOOGL"
)
compare_tickers = [t.strip().upper() for t in compare_input.split(",") if t.strip()]

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh data"):
    st.cache_data.clear()

st.sidebar.caption(
    "Data provided by Yahoo Finance via the `yfinance` library. "
    "Prices may be delayed and are for informational purposes only."
)

# ----------------------------------------------------------------------------
# Main page
# ----------------------------------------------------------------------------
st.title("📈 Stock Market Dashboard")

if not ticker_input:
    st.warning("Enter a ticker symbol in the sidebar to get started.")
    st.stop()

with st.spinner(f"Loading data for {ticker_input}..."):
    history = load_price_history(ticker_input, period, interval)
    info = load_company_info(ticker_input)

if history.empty:
    st.error(f"No data found for ticker '{ticker_input}'. Please check the symbol and try again.")
    st.stop()

history = add_moving_averages(history)
history["RSI"] = compute_rsi(history)

# ---- Header: company name + key metrics ----
company_name = info.get("longName") or info.get("shortName") or ticker_input
st.subheader(f"{company_name} ({ticker_input})")

last_close = history["Close"].iloc[-1]
prev_close = history["Close"].iloc[-2] if len(history) > 1 else last_close
change = last_close - prev_close
pct_change = (change / prev_close * 100) if prev_close else 0

metric_cols = st.columns(6)
metric_cols[0].metric(
    "Last Price",
    f"${last_close:,.2f}",
    f"{change:+.2f} ({pct_change:+.2f}%)",
)
metric_cols[1].metric("Day High", f"${history['High'].iloc[-1]:,.2f}")
metric_cols[2].metric("Day Low", f"${history['Low'].iloc[-1]:,.2f}")
metric_cols[3].metric("Volume", format_large_number(history["Volume"].iloc[-1]))
metric_cols[4].metric("Market Cap", format_large_number(info.get("marketCap")))
pe_ratio = info.get("trailingPE")
metric_cols[5].metric("P/E Ratio", f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else "N/A")

st.markdown("---")

# ---- Price chart ----
row_heights = [0.6]
specs = [[{"secondary_y": False}]]
subplot_titles = ["Price"]

n_rows = 1
if show_volume:
    n_rows += 1
    row_heights.append(0.2)
    subplot_titles.append("Volume")
if show_rsi:
    n_rows += 1
    row_heights.append(0.2)
    subplot_titles.append("RSI (14)")

total = sum(row_heights)
row_heights = [h / total for h in row_heights]

fig = make_subplots(
    rows=n_rows,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.03,
    row_heights=row_heights,
    subplot_titles=subplot_titles,
)

if chart_type == "Candlestick":
    fig.add_trace(
        go.Candlestick(
            x=history.index,
            open=history["Open"],
            high=history["High"],
            low=history["Low"],
            close=history["Close"],
            name=ticker_input,
        ),
        row=1,
        col=1,
    )
else:
    fig.add_trace(
        go.Scatter(x=history.index, y=history["Close"], mode="lines", name=ticker_input),
        row=1,
        col=1,
    )

if show_sma:
    fig.add_trace(
        go.Scatter(x=history.index, y=history["SMA20"], mode="lines", name="SMA 20", line=dict(width=1.5)),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=history.index, y=history["SMA50"], mode="lines", name="SMA 50", line=dict(width=1.5)),
        row=1,
        col=1,
    )

current_row = 2
if show_volume:
    colors = [
        "green" if c >= o else "red"
        for c, o in zip(history["Close"], history["Open"])
    ]
    fig.add_trace(
        go.Bar(x=history.index, y=history["Volume"], name="Volume", marker_color=colors),
        row=current_row,
        col=1,
    )
    current_row += 1

if show_rsi:
    fig.add_trace(
        go.Scatter(x=history.index, y=history["RSI"], mode="lines", name="RSI", line=dict(color="orange")),
        row=current_row,
        col=1,
    )
    fig.add_hline(y=70, line_dash="dot", line_color="red", row=current_row, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="green", row=current_row, col=1)

fig.update_layout(
    height=750,
    xaxis_rangeslider_visible=False,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(t=40, b=20, l=10, r=10),
)

st.plotly_chart(fig, use_container_width=True)

# ---- Multi-stock comparison ----
if compare_tickers:
    st.markdown("---")
    st.subheader("📊 Normalized Performance Comparison")
    st.caption("All series are indexed to 100 at the start of the selected period, so relative performance is easy to compare.")

    all_tickers = [ticker_input] + [t for t in compare_tickers if t != ticker_input]
    comp_fig = go.Figure()

    for t in all_tickers:
        df = load_price_history(t, period, interval)
        if df.empty:
            st.warning(f"Could not load data for '{t}' — skipping.")
            continue
        normalized = df["Close"] / df["Close"].iloc[0] * 100
        comp_fig.add_trace(go.Scatter(x=df.index, y=normalized, mode="lines", name=t))

    comp_fig.update_layout(
        height=450,
        yaxis_title="Indexed Price (start = 100)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=20, b=20, l=10, r=10),
    )
    st.plotly_chart(comp_fig, use_container_width=True)

# ---- Raw data table ----
with st.expander("📄 View raw historical data"):
    st.dataframe(history.sort_index(ascending=False), use_container_width=True)
    csv = history.to_csv().encode("utf-8")
    st.download_button(
        "Download data as CSV",
        data=csv,
        file_name=f"{ticker_input}_history.csv",
        mime="text/csv",
    )

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Data source: Yahoo Finance")
