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


def calculate_rsi(prices, period=14):
    """Calculate 14-day RSI without requiring another package."""

    delta = prices.diff()

    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    average_gain = gains.rolling(period).mean()
    average_loss = losses.rolling(period).mean()

    rs = average_gain / average_loss.replace(0, float("nan"))

    rsi = 100 - (100 / (1 + rs))

    return rsi


def score_drawdown(drawdown):
    """
    Maximum 30 points.

    Larger drawdown = more crash potential.
    """

    if drawdown <= -50:
        return 30
    elif drawdown <= -40:
        return 27
    elif drawdown <= -30:
        return 24
    elif drawdown <= -25:
        return 20
    elif drawdown <= -20:
        return 16
    elif drawdown <= -15:
        return 10
    elif drawdown <= -10:
        return 5
    else:
        return 0


def score_rsi(rsi):
    """
    Maximum 20 points.

    Oversold conditions receive higher scores.
    """

    if rsi <= 25:
        return 20
    elif rsi <= 30:
        return 17
    elif rsi <= 35:
        return 13
    elif rsi <= 40:
        return 8
    elif rsi <= 45:
        return 4
    else:
        return 0


def score_1m_return(return_1m):
    """
    Maximum 15 points.

    Significant recent declines receive higher scores.
    """

    if return_1m <= -30:
        return 15
    elif return_1m <= -20:
        return 12
    elif return_1m <= -15:
        return 9
    elif return_1m <= -10:
        return 6
    elif return_1m <= -5:
        return 3
    else:
        return 0


def score_3m_return(return_3m):
    """
    Maximum 15 points.

    Significant 3-month declines receive higher scores.
    """

    if return_3m <= -40:
        return 15
    elif return_3m <= -30:
        return 12
    elif return_3m <= -20:
        return 9
    elif return_3m <= -15:
        return 6
    elif return_3m <= -10:
        return 3
    else:
        return 0


def score_volume(volume_ratio):
    """
    Maximum 10 points.

    High volume can indicate unusually strong market interest.
    """

    if volume_ratio >= 3:
        return 10
    elif volume_ratio >= 2:
        return 8
    elif volume_ratio >= 1.5:
        return 6
    elif volume_ratio >= 1.2:
        return 3
    else:
        return 0


def score_stabilization(return_5d, return_1m):
    """
    Maximum 10 points.

    We don't want to blindly buy a stock that is still
    falling aggressively.

    A stock gets more points when the recent 5-day movement
    shows stabilization relative to the larger 1-month fall.
    """

    if return_5d >= 0:
        return 10
    elif return_5d >= -2:
        return 8
    elif return_5d >= -5:
        return 5
    elif return_5d >= -10:
        return 2
    else:
        return 0


print("=" * 80)
print("NASDAQ-100 CRASH BUYING AGENT")
print("=" * 80)

print("Date:", datetime.now().strftime("%Y-%m-%d"))
print("Downloading 1 year of daily market data...")
print()

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

        if len(stock) < 100:
            print(f"{ticker}: insufficient data")
            continue

        close = stock["Close"]
        high = stock["High"]
        volume = stock["Volume"]

        current_price = float(close.iloc[-1])

        # --------------------------------------------------
        # 52 WEEK DRAWDOWN
        # --------------------------------------------------

        high_52_week = float(high.max())

        drawdown = (
            (current_price - high_52_week)
            / high_52_week
        ) * 100

        # --------------------------------------------------
        # RETURNS
        # --------------------------------------------------

        price_5d = float(close.iloc[-6])
        price_1m = float(close.iloc[-22])
        price_3m = float(close.iloc[-64])

        return_5d = ((current_price - price_5d) / price_5d) * 100
        return_1m = ((current_price - price_1m) / price_1m) * 100
        return_3m = ((current_price - price_3m) / price_3m) * 100

        # --------------------------------------------------
        # RSI
        # --------------------------------------------------

        rsi_series = calculate_rsi(close)

        rsi = float(rsi_series.iloc[-1])

        # --------------------------------------------------
        # VOLUME
        # --------------------------------------------------

        average_volume = float(volume.iloc[-21:-1].mean())

        current_volume = float(volume.iloc[-1])

        if average_volume > 0:
            volume_ratio = current_volume / average_volume
        else:
            volume_ratio = 0

        # --------------------------------------------------
        # SCORE EACH FACTOR
        # --------------------------------------------------

        drawdown_score = score_drawdown(drawdown)

        rsi_score = score_rsi(rsi)

        one_month_score = score_1m_return(return_1m)

        three_month_score = score_3m_return(return_3m)

        volume_score = score_volume(volume_ratio)

        stabilization_score = score_stabilization(
            return_5d,
            return_1m
        )

        # --------------------------------------------------
        # TOTAL SCORE
        # --------------------------------------------------

        total_score = (
            drawdown_score
            + rsi_score
            + one_month_score
            + three_month_score
            + volume_score
            + stabilization_score
        )

        results.append({

            "Ticker": ticker,

            "Price": current_price,

            "Drawdown": drawdown,

"5D": return_5d,

"1M": return_1m,

"3M": return_3m,

"RSI": rsi,

            "VolRatio": volume_ratio,

            "Score": total_score

        })

    except Exception as e:

        print(f"{ticker}: ERROR - {e}")


# ----------------------------------------------------------
# CREATE RESULTS TABLE
# ----------------------------------------------------------

df = pd.DataFrame(results)

df = df.sort_values(
    "Score",
    ascending=False
)


print()
print("=" * 80)
print("CRASH BUYING SCORE")
print("=" * 80)

print(
    df.to_string(
        index=False,
        formatters={

            "Price": "{:.2f}".format,

            "Drawdown": "{:.2f}%".format,

            "1M": "{:.2f}%".format,

            "3M": "{:.2f}%".format,

            "RSI": "{:.1f}".format,

            "VolRatio": "{:.2f}x".format,

            "Score": "{:.0f}".format

        }
    )
)


# ----------------------------------------------------------
# TOP 10
# ----------------------------------------------------------

print()
print("=" * 80)
print("TOP 10 CRASH BUYING CANDIDATES")
print("=" * 80)

top10 = df.head(10)

print(
    top10.to_string(
        index=False,
        formatters={

            "Price": "{:.2f}".format,

            "Drawdown": "{:.2f}%".format,

            "1M": "{:.2f}%".format,

            "3M": "{:.2f}%".format,

            "RSI": "{:.1f}".format,

            "VolRatio": "{:.2f}x".format,

            "Score": "{:.0f}".format

        }
    )
)

# ----------------------------------------------------------
# TOP 3 CRASH BUYING CANDIDATES
# ----------------------------------------------------------

print()
print("=" * 80)
print("TOP 3 CRASH BUYING CANDIDATES")
print("=" * 80)


def generate_reasons(row):

    reasons = []

    # Drawdown
    if row["Drawdown"] <= -50:
        reasons.append(
            "Very large decline from the 52-week high"
        )
    elif row["Drawdown"] <= -30:
        reasons.append(
            "Large decline from the 52-week high"
        )
    elif row["Drawdown"] <= -20:
        reasons.append(
            "Significant decline from the 52-week high"
        )

    # RSI
    if row["RSI"] <= 25:
        reasons.append(
            "Extremely oversold RSI"
        )
    elif row["RSI"] <= 30:
        reasons.append(
            "Strongly oversold RSI"
        )
    elif row["RSI"] <= 35:
        reasons.append(
            "Oversold RSI"
        )

    # 1 month
    if row["1M"] <= -20:
        reasons.append(
            "Very large 1-month decline"
        )
    elif row["1M"] <= -10:
        reasons.append(
            "Significant 1-month decline"
        )

    # 3 month
    if row["3M"] <= -30:
        reasons.append(
            "Very large 3-month decline"
        )
    elif row["3M"] <= -20:
        reasons.append(
            "Significant 3-month decline"
        )

    # Volume
    if row["VolRatio"] >= 2:
        reasons.append(
            "Unusually high trading volume"
        )
    elif row["VolRatio"] >= 1.5:
        reasons.append(
            "Above-average trading volume"
        )

    # Stabilization
    if row["5D"] >= 0:
        reasons.append(
            "Recent 5-day price action shows stabilization"
        )
    elif row["5D"] >= -2:
        reasons.append(
            "Recent selling pressure is slowing"
        )

    if not reasons:
        reasons.append(
            "Strongest overall crash-buying score in the Nasdaq-100"
        )

    return reasons


# ----------------------------------------------------------
# ADD 5-DAY RETURN TO RESULTS
# ----------------------------------------------------------

if "5D" not in df.columns:

    df["5D"] = 0.0


# Recalculate ranking after adding the 5-day data
df = df.sort_values(
    "Score",
    ascending=False
)


top3 = df.head(3)


for rank, (_, row) in enumerate(
    top3.iterrows(),
    start=1
):

    print()

    print(f"#{rank} {row['Ticker']}")

    print(
        f"Crash Buying Score: "
        f"{row['Score']:.0f}/100"
    )

    print(
        f"Current Price: "
        f"${row['Price']:.2f}"
    )

    print(
        f"52W Drawdown: "
        f"{row['Drawdown']:.2f}%"
    )

    print(
        f"1 Month: "
        f"{row['1M']:.2f}%"
    )

    print(
        f"3 Months: "
        f"{row['3M']:.2f}%"
    )

    print(
        f"RSI: "
        f"{row['RSI']:.1f}"
    )

    print(
        f"Volume vs 20D Average: "
        f"{row['VolRatio']:.2f}x"
    )

    print()

    print("WHY THIS STOCK WAS SELECTED:")

    reasons = generate_reasons(row)

    for reason in reasons:
        print(f"  ✓ {reason}")


# ----------------------------------------------------------
# STAGE 5 - OPPORTUNITY FILTER
# ----------------------------------------------------------

print()
print("=" * 80)
print("STAGE 5 - CRASH BUYING OPPORTUNITY FILTER")
print("=" * 80)

# Minimum requirements for a strong crash-buying opportunity
MIN_SCORE = 55
MIN_DRAWDOWN = -20
MAX_RSI = 40


def is_strong_opportunity(row):

    score_ok = row["Score"] >= MIN_SCORE

    drawdown_ok = row["Drawdown"] <= MIN_DRAWDOWN

    rsi_ok = row["RSI"] <= MAX_RSI

    # Require at least the score and drawdown conditions.
    # RSI is an additional confirmation rather than an absolute requirement.
    return score_ok and drawdown_ok


# Check the Top 3
opportunities = []

for _, row in top3.iterrows():

    if is_strong_opportunity(row):
        opportunities.append(row)


print()

if len(opportunities) > 0:

    print("🟢 STRONG CRASH-BUYING OPPORTUNITY FOUND")

    print()
    print(
        f"{len(opportunities)} of the Top 3 candidates "
        "passed the opportunity filter."
    )

    print()

    for rank, (_, row) in enumerate(
        top3.iterrows(),
        start=1
    ):

        status = (
            "PASS"
            if is_strong_opportunity(row)
            else "WATCH"
        )

        print(
            f"#{rank} {row['Ticker']} "
            f"- {status}"
        )

        print(
            f"   Score: {row['Score']:.0f}/100"
        )

        print(
            f"   Drawdown: {row['Drawdown']:.2f}%"
        )

        print(
            f"   RSI: {row['RSI']:.1f}"
        )

        print()

else:

    print("⚪ NO STRONG CRASH-BUYING OPPORTUNITY TODAY")

    print()
    print(
        "The Nasdaq-100 was scanned, but none of "
        "the Top 3 candidates passed the minimum "
        "crash-buying conditions."
    )

print()
print("=" * 80)
print("STAGE 5 FILTER COMPLETED")
print("=" * 80)

# ----------------------------------------------------------
# EMAIL ALERT CONTENT
# ----------------------------------------------------------

email_lines = []

email_lines.append(
    "NASDAQ-100 CRASH BUYING ALERT"
)

email_lines.append(
    "=" * 60
)

email_lines.append(
    f"Scan date: {datetime.now().strftime('%Y-%m-%d')}"
)

email_lines.append("")

if len(opportunities) > 0:

    email_lines.append(
        "STRONG CRASH-BUYING OPPORTUNITY FOUND"
    )

    email_lines.append("")

    email_lines.append(
        "Top candidates from the Nasdaq-100:"
    )

    email_lines.append("")

    for rank, (_, row) in enumerate(
        top3.iterrows(),
        start=1
    ):

        status = (
            "PASS"
            if is_strong_opportunity(row)
            else "WATCH"
        )

        email_lines.append(
            f"#{rank} {row['Ticker']} - {status}"
        )

        email_lines.append(
            f"Crash Buying Score: "
            f"{row['Score']:.0f}/100"
        )

        email_lines.append(
            f"Current Price: "
            f"${row['Price']:.2f}"
        )

        email_lines.append(
            f"52W Drawdown: "
            f"{row['Drawdown']:.2f}%"
        )

        email_lines.append(
            f"1 Month: "
            f"{row['1M']:.2f}%"
        )

        email_lines.append(
            f"3 Months: "
            f"{row['3M']:.2f}%"
        )

        email_lines.append(
            f"RSI: "
            f"{row['RSI']:.1f}"
        )

        email_lines.append(
            f"Volume vs 20D Average: "
            f"{row['VolRatio']:.2f}x"
        )

        email_lines.append("")

        email_lines.append(
            "Why selected:"
        )

        reasons = generate_reasons(row)

        for reason in reasons:

            email_lines.append(
                f"  - {reason}"
            )

        email_lines.append("")

        email_lines.append(
            "-" * 60
        )

        email_lines.append("")

else:

    email_lines.append(
        "NO STRONG CRASH-BUYING OPPORTUNITY TODAY"
    )

    email_lines.append("")

    email_lines.append(
        "No Top-3 candidate passed the minimum "
        "crash-buying conditions."
    )


email_lines.append("")

email_lines.append(
    "IMPORTANT:"
)

email_lines.append(
    "This is an automated screening signal, "
    "not financial advice or an automatic buy instruction."
)

email_lines.append(
    "Further fundamental analysis is required before "
    "making any investment decision."
)


EMAIL_SUBJECT = (
    "NASDAQ-100 Crash Buying Alert - "
    + datetime.now().strftime("%Y-%m-%d")
)

EMAIL_BODY = "\n".join(email_lines)

print()
print("=" * 80)
print("EMAIL ALERT PREVIEW")
print("=" * 80)

print(EMAIL_BODY)
