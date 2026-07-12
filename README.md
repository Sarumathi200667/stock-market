An interactive stock market dashboard built with **Streamlit**, **yfinance**, and **Plotly**.

## Features

- Live price data for any public ticker (via Yahoo Finance)
- Candlestick or line price charts
- 20-day and 50-day simple moving averages
- RSI (Relative Strength Index) indicator with overbought/oversold lines
- Volume chart, colored by up/down days
- Key metrics: last price, day change, day high/low, volume, market cap, P/E ratio
- Multi-stock normalized comparison chart (indexed to 100)
- Adjustable time period and interval (5 days up to max history)
- Downloadable CSV of the raw historical data
- 5-minute data caching, with a manual refresh button

## Setup

1. **Install Python 3.9+** if you don't already have it.

2. **Install the dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the dashboard:**

   ```bash
   streamlit run app.py
   ```

4. Streamlit will open the dashboard automatically in your browser
   (usually at `http://localhost:8501`).

## Usage

- Enter any valid ticker symbol (e.g. `AAPL`, `TSLA`, `MSFT`, `GOOGL`, `AMZN`) in the sidebar.
- Choose a time period and chart type.
- Toggle moving averages, RSI, and volume on/off.
- Add comma-separated tickers under "Compare with other tickers" to see a
  normalized performance comparison against your primary ticker.
- Click "🔄 Refresh data" to bypass the 5-minute cache and pull the latest prices.
- Expand "View raw historical data" to see/download the underlying OHLCV data.

## Notes

- Data comes from Yahoo Finance via the `yfinance` library and can be delayed;
  this dashboard is for informational/educational purposes only and is not
  financial advice.
- If a ticker returns no data, double-check the symbol — some symbols use
  exchange suffixes (e.g. `TCS.NS` for NSE-listed stocks, `SHOP.TO` for TSX).

## Possible extensions

- Add technical indicators like MACD or Bollinger Bands
- Add a watchlist saved to a local file or database
- Add earnings dates, dividends, or news headlines
- Deploy to Streamlit Community Cloud for a shareable public link# stock-market
