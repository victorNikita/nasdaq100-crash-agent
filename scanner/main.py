import yfinance as yf
import pandas as pd
from datetime import datetime

NASDAQ_100 = [
    "AAPL", "ABNB", "ADBE", "ADI", "ADP", "ADSK", "AEP",
    "ALNY", "AMAT", "AMD", "AMGN", "AMZN", "APP", "ARM",
    "ASML", "AVGO", "AXON", "BKR", "BKNG", "CCEP", "CDNS",
    "CEG", "CHTR", "CMCSA", "COST", "CPRT", "CRWD", "CSCO",
    "CSGP", "CSX", "CTAS", "DASH", "DDOG", "DXCM", "EA",
    "EXC", "FANG", "FAST", "FER", "FTNT", "GEHC", "GILD",
    "GOOG", "GOOGL", "HON", "IDXX", "INTC", "INTU", "ISRG",
    "KDP", "KHC", "KLAC", "LIN", "LRCX", "MAR", "MCHP",
    "MDLZ", "MELI", "META", "MNST", "MPWR", "MRVL", "MSFT",
    "MSTR", "MU", "NFLX", "NVDA", "NXPI", "ODFL", "ORLY",
    "PANW", "PAYX", "PCAR", "PDD", "PEP", "PLTR", "PYPL",
    "QCOM", "REGN", "ROP", "ROST", "SBUX", "SHOP", "SNPS",
    "STX", "TEAM", "TER", "TMUS", "TSLA", "TTWO", "TXN",
    "WDC", "WMT", "XEL", "ZS", "ALAB", "CRWV", "NBIS",
    "RKLB"
]

print("=" * 70)
print("NASDAQ-100 CRASH BUYING AGENT")
print("=" * 70)
print("Date:", datetime.now().strftime("%Y-%m-%d"))
print("Downloading 1 year of daily market data...")
print()

# Download one year of data for all stocks
data = yf.download(
    NASDAQ_100,
    period="1y",
    interval="1d",
    auto_adjust=True,
    group_by="ticker",
    threads=True,
    progress=False
)

results = []

for ticker in NASDAQ_100:

    try:
        stock = data[ticker].dropna()

        if stock.empty:
            print(f"{ticker}: No data")
            continue

        current_price = float(stock["Close"].iloc[-1])
        high_52_week = float(stock["High"].max())

        drawdown = ((current_price - high_52_week) / high_52_week) * 100

        results.append({
            "Ticker": ticker,
            "Price": current_price,
            "52W_High": high_52_week,
            "Drawdown": drawdown
        })

    except Exception as e:
        print(f"{ticker}: ERROR - {e}")

# Convert to DataFrame
df = pd.DataFrame(results)

# Sort from biggest fall to smallest fall
df = df.sort_values("Drawdown")

print()
print("=" * 70)
print("NASDAQ-100 PRICE / 52-WEEK HIGH ANALYSIS")
print("=" * 70)

print(
    df.to_string(
        index=False,
        formatters={
            "Price": "{:.2f}".format,
            "52W_High": "{:.2f}".format,
            "Drawdown": "{:.2f}%".format
        }
    )
)

print()
print("=" * 70)
print("LARGEST 10 DRAWDOWNS")
print("=" * 70)

print(
    df.head(10).to_string(
        index=False,
        formatters={
            "Price": "{:.2f}".format,
            "52W_High": "{:.2f}".format,
            "Drawdown": "{:.2f}%".format
        }
    )
)

print()
print("Scan completed successfully.")
