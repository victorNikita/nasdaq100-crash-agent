import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_alert(subject, body):

    email_username = os.environ.get("EMAIL_USERNAME")
    email_password = os.environ.get("EMAIL_PASSWORD")

    if not email_username or not email_password:
        print("EMAIL ERROR: Email credentials not found.")
        return

    message = MIMEMultipart()
    message["From"] = email_username
    message["To"] = email_username
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    try:

        with smtplib.SMTP("smtp.gmail.com", 587) as server:

            server.starttls()

            server.login(
                email_username,
                email_password
            )

            server.sendmail(
                email_username,
                email_username,
                message.as_string()
            )

        print("EMAIL SENT SUCCESSFULLY")

    except Exception as e:

        print("EMAIL ERROR:", e)

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

# ----------------------------------------------------------
# STAGE 6 - FUNDAMENTAL ANALYSIS
# ----------------------------------------------------------

print()
print("=" * 80)
print("STAGE 6 - FUNDAMENTAL ANALYSIS")
print("=" * 80)

print()
print("Checking financial health of the leading crash candidates...")
print()


def safe_float(value):
    """Safely convert a value to float."""

    try:
        if pd.isna(value):
            return None

        return float(value)

    except Exception:
        return None


def get_latest_value(statement, possible_names):
    """
    Find the latest available value from a financial statement.

    Different companies sometimes use slightly different
    accounting labels, so we try several possibilities.
    """

    if statement is None or statement.empty:
        return None

    for name in possible_names:

        if name in statement.index:

            series = statement.loc[name].dropna()

            if len(series) > 0:

                return safe_float(series.iloc[0])

    return None


def get_previous_value(statement, possible_names):
    """Find the second-most-recent available value."""

    if statement is None or statement.empty:
        return None

    for name in possible_names:

        if name in statement.index:

            series = statement.loc[name].dropna()

            if len(series) > 1:

                return safe_float(series.iloc[1])

    return None


def calculate_growth(current, previous):
    """Calculate percentage growth."""

    if current is None or previous is None:
        return None

    if previous == 0:
        return None

    return ((current - previous) / abs(previous)) * 100


def fundamental_score_revenue(growth):
    """Revenue growth score: maximum 10 points."""

    if growth is None:
        return 0

    if growth >= 20:
        return 10
    elif growth >= 10:
        return 8
    elif growth >= 5:
        return 6
    elif growth >= 0:
        return 4
    elif growth >= -5:
        return 2
    else:
        return 0


def fundamental_score_earnings(growth):
    """Earnings growth score: maximum 10 points."""

    if growth is None:
        return 0

    if growth >= 25:
        return 10
    elif growth >= 15:
        return 8
    elif growth >= 5:
        return 6
    elif growth >= 0:
        return 4
    elif growth >= -10:
        return 2
    else:
        return 0


def fundamental_score_fcf(fcf):
    """Free cash flow score: maximum 10 points."""

    if fcf is None:
        return 0

    if fcf > 0:
        return 10

    return 0


def fundamental_score_balance_sheet(cash, debt):
    """Balance-sheet score: maximum 10 points."""

    if cash is None or debt is None:
        return 0

    if debt <= 0:
        return 10

    ratio = cash / debt

    if ratio >= 2:
        return 10
    elif ratio >= 1:
        return 8
    elif ratio >= 0.5:
        return 5
    elif ratio >= 0.25:
        return 3
    else:
        return 0

# ----------------------------------------------------------
# ANALYSE TOP TECHNICAL CANDIDATES
# ----------------------------------------------------------

# We don't need to download detailed financial statements
# for every Nasdaq-100 company.
#
# First identify the strongest technical candidates,
# then perform deeper fundamental analysis on those stocks.

technical_candidates = df.head(10).copy()

fundamental_results = []


for _, row in technical_candidates.iterrows():

    ticker = row["Ticker"]

    print()
    print(f"Analysing fundamentals: {ticker}")

    try:

        company = yf.Ticker(ticker)

        income_statement = company.income_stmt

        balance_sheet = company.balance_sheet

        cash_flow = company.cashflow

        # --------------------------------------------------
        # REVENUE
        # --------------------------------------------------

        revenue_current = get_latest_value(
            income_statement,
            [
                "Total Revenue",
                "Operating Revenue"
            ]
        )

        revenue_previous = get_previous_value(
            income_statement,
            [
                "Total Revenue",
                "Operating Revenue"
            ]
        )

        revenue_growth = calculate_growth(
            revenue_current,
            revenue_previous
        )

        # --------------------------------------------------
        # NET INCOME
        # --------------------------------------------------

        earnings_current = get_latest_value(
            income_statement,
            [
                "Net Income",
                "Net Income Common Stockholders"
            ]
        )

        earnings_previous = get_previous_value(
            income_statement,
            [
                "Net Income",
                "Net Income Common Stockholders"
            ]
        )

        earnings_growth = calculate_growth(
            earnings_current,
            earnings_previous
        )

        # --------------------------------------------------
        # FREE CASH FLOW
        # --------------------------------------------------

        operating_cash_flow = get_latest_value(
            cash_flow,
            [
                "Operating Cash Flow",
                "Total Cash From Operating Activities"
            ]
        )

        capital_expenditure = get_latest_value(
            cash_flow,
            [
                "Capital Expenditure",
                "Capital Expenditures"
            ]
        )

        if (
            operating_cash_flow is not None
            and capital_expenditure is not None
        ):

            # Capital expenditure is normally negative
            # in the cash-flow statement.

            free_cash_flow = (
                operating_cash_flow
                + capital_expenditure
            )

        else:

            free_cash_flow = None

        # --------------------------------------------------
        # CASH
        # --------------------------------------------------

        cash = get_latest_value(
            balance_sheet,
            [
                "Cash Cash Equivalents And Short Term Investments",
                "Cash And Cash Equivalents",
                "Cash Financial"
            ]
        )

        # --------------------------------------------------
        # TOTAL DEBT
        # --------------------------------------------------

        debt = get_latest_value(
            balance_sheet,
            [
                "Total Debt",
                "Long Term Debt And Capital Lease Obligation",
                "Long Term Debt"
            ]
        )

        # --------------------------------------------------
        # SCORE
        # --------------------------------------------------

        revenue_score = fundamental_score_revenue(
            revenue_growth
        )

        earnings_score = fundamental_score_earnings(
            earnings_growth
        )

        fcf_score = fundamental_score_fcf(
            free_cash_flow
        )

        balance_score = fundamental_score_balance_sheet(
            cash,
            debt
        )

        fundamental_score = (
            revenue_score
            + earnings_score
            + fcf_score
            + balance_score
        )

        fundamental_results.append({

            "Ticker": ticker,

            "RevenueGrowth": revenue_growth,

            "EarningsGrowth": earnings_growth,

            "FCF": free_cash_flow,

            "Cash": cash,

            "Debt": debt,

            "FundamentalScore": fundamental_score

        })

    except Exception as e:

        print(
            f"{ticker}: fundamental analysis error - {e}"
        )

        fundamental_results.append({

            "Ticker": ticker,

            "RevenueGrowth": None,

            "EarningsGrowth": None,

            "FCF": None,

            "Cash": None,

            "Debt": None,

            "FundamentalScore": 0

        })


# ----------------------------------------------------------
# MERGE FUNDAMENTAL DATA WITH TECHNICAL DATA
# ----------------------------------------------------------

fundamental_df = pd.DataFrame(
    fundamental_results
)

df = df.merge(
    fundamental_df,
    on="Ticker",
    how="left"
)


print()
print("=" * 80)
print("FUNDAMENTAL ANALYSIS RESULTS")
print("=" * 80)


fundamental_display = df[
    [
        "Ticker",
        "Score",
        "FundamentalScore",
        "RevenueGrowth",
        "EarningsGrowth",
        "FCF",
        "Cash",
        "Debt"
    ]
].copy()


print(
    fundamental_display.to_string(
        index=False,
        formatters={

            "Score": "{:.0f}".format,

            "FundamentalScore": "{:.0f}".format,

            "RevenueGrowth":
                lambda x:
                "N/A"
                if pd.isna(x)
                else f"{x:.1f}%",

            "EarningsGrowth":
                lambda x:
                "N/A"
                if pd.isna(x)
                else f"{x:.1f}%",

            "FCF":
                lambda x:
                "N/A"
                if pd.isna(x)
                else f"${x:,.0f}",

            "Cash":
                lambda x:
                "N/A"
                if pd.isna(x)
                else f"${x:,.0f}",

            "Debt":
                lambda x:
                "N/A"
                if pd.isna(x)
                else f"${x:,.0f}"

        }
    )
)


print()
print("=" * 80)
print("STAGE 6 FUNDAMENTAL ANALYSIS COMPLETED")
print("=" * 80)

# ----------------------------------------------------------
# STAGE 7 - COMBINED CRASH BUYING SCORE
# ----------------------------------------------------------

print()
print("=" * 80)
print("STAGE 7 - COMBINED CRASH BUYING SCORE")
print("=" * 80)


# ----------------------------------------------------------
# NORMALISE FUNDAMENTAL SCORE
# ----------------------------------------------------------
#
# Fundamental score maximum = 40
# Convert it to a 100-point scale.
#

df["FundamentalScore100"] = (
    df["FundamentalScore"] / 40
) * 100


# ----------------------------------------------------------
# COMBINE TECHNICAL + FUNDAMENTAL SCORES
# ----------------------------------------------------------
#
# Technical weight     = 60%
# Fundamental weight   = 40%
#

df["FinalScore"] = (
    df["Score"] * 0.60
    +
    df["FundamentalScore100"] * 0.40
)


# ----------------------------------------------------------
# FUNDAMENTAL RISK FLAG
# ----------------------------------------------------------

def fundamental_risk(row):

    score = row["FundamentalScore"]

    revenue = row["RevenueGrowth"]

    earnings = row["EarningsGrowth"]

    fcf = row["FCF"]

    # Very weak fundamentals
    if score < 15:

        return "HIGH FUNDAMENTAL RISK"

    # Deteriorating revenue and earnings
    if (
        pd.notna(revenue)
        and pd.notna(earnings)
        and revenue < 0
        and earnings < 0
    ):

        return "FUNDAMENTAL DETERIORATION"

    # Negative free cash flow
    if (
        pd.notna(fcf)
        and fcf < 0
        and score < 25
    ):

        return "CASH FLOW RISK"

    return "HEALTHY / ACCEPTABLE"


df["FundamentalRisk"] = df.apply(
    fundamental_risk,
    axis=1
)


# ----------------------------------------------------------
# SORT BY FINAL SCORE
# ----------------------------------------------------------

df = df.sort_values(
    "FinalScore",
    ascending=False
)


# ----------------------------------------------------------
# DISPLAY COMBINED RANKING
# ----------------------------------------------------------

print()
print(
    "FINAL NASDAQ-100 CRASH BUYING RANKING"
)

print()

display_columns = [
    "Ticker",
    "Score",
    "FundamentalScore",
    "FinalScore",
    "Drawdown",
    "RSI",
    "RevenueGrowth",
    "EarningsGrowth",
    "FundamentalRisk"
]


print(
    df[display_columns].head(10).to_string(
        index=False,

        formatters={

            "Score":
                "{:.0f}".format,

            "FundamentalScore":
                "{:.0f}".format,

            "FinalScore":
                "{:.1f}".format,

            "Drawdown":
                "{:.2f}%".format,

            "RSI":
                "{:.1f}".format,

            "RevenueGrowth":
                lambda x:
                "N/A"
                if pd.isna(x)
                else f"{x:.1f}%",

            "EarningsGrowth":
                lambda x:
                "N/A"
                if pd.isna(x)
                else f"{x:.1f}%"

        }
    )
)


# ----------------------------------------------------------
# FINAL TOP 3
# ----------------------------------------------------------

final_top3 = df.head(3)


print()
print("=" * 80)
print("FINAL TOP 3 CRASH BUYING OPPORTUNITIES")
print("=" * 80)


for rank, (_, row) in enumerate(
    final_top3.iterrows(),
    start=1
):

    print()

    print(
        f"#{rank} {row['Ticker']}"
    )

    print(
        f"Final Crash Buying Score: "
        f"{row['FinalScore']:.1f}/100"
    )

    print(
        f"Technical Score: "
        f"{row['Score']:.0f}/100"
    )

    print(
        f"Fundamental Score: "
        f"{row['FundamentalScore']:.0f}/40"
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
        f"RSI: "
        f"{row['RSI']:.1f}"
    )

    print(
        f"Revenue Growth: "
        + (
            "N/A"
            if pd.isna(row["RevenueGrowth"])
            else f"{row['RevenueGrowth']:.1f}%"
        )
    )

    print(
        f"Earnings Growth: "
        + (
            "N/A"
            if pd.isna(row["EarningsGrowth"])
            else f"{row['EarningsGrowth']:.1f}%"
        )
    )

    print(
        f"Fundamental Assessment: "
        f"{row['FundamentalRisk']}"
    )


print()
print("=" * 80)
print("STAGE 7 COMPLETED")
print("=" * 80)

# ----------------------------------------------------------
# STAGE 8 - AI-STYLE CANDIDATE EXPLANATION
# ----------------------------------------------------------

print()
print("=" * 80)
print("STAGE 8 - CANDIDATE EXPLANATIONS")
print("=" * 80)


def create_candidate_explanation(row):

    strengths = []
    risks = []

    # ------------------------------------------------------
    # TECHNICAL STRENGTHS
    # ------------------------------------------------------

    if row["Drawdown"] <= -50:

        strengths.append(
            "The stock has experienced a very large "
            "decline from its 52-week high."
        )

    elif row["Drawdown"] <= -30:

        strengths.append(
            "The stock has experienced a large decline "
            "from its 52-week high."
        )

    elif row["Drawdown"] <= -20:

        strengths.append(
            "The stock has experienced a significant "
            "decline from its 52-week high."
        )


    if row["RSI"] <= 30:

        strengths.append(
            "The RSI indicates strongly oversold conditions."
        )

    elif row["RSI"] <= 40:

        strengths.append(
            "The RSI indicates that selling has pushed "
            "the stock toward oversold territory."
        )


    if row["1M"] <= -20:

        strengths.append(
            "The stock has suffered a significant "
            "one-month decline."
        )

    elif row["1M"] <= -10:

        strengths.append(
            "The stock has experienced notable "
            "one-month selling pressure."
        )


    if row["VolRatio"] >= 2:

        strengths.append(
            "Trading volume is substantially above "
            "its recent average."
        )

    elif row["VolRatio"] >= 1.5:

        strengths.append(
            "Trading volume is above its recent average."
        )


    if row["5D"] >= 0:

        strengths.append(
            "Recent five-day price action suggests "
            "some stabilization."
        )

    elif row["5D"] >= -2:

        strengths.append(
            "Recent selling pressure appears to be slowing."
        )


    # ------------------------------------------------------
    # FUNDAMENTAL STRENGTHS
    # ------------------------------------------------------

    revenue_growth = row["RevenueGrowth"]

    earnings_growth = row["EarningsGrowth"]

    fcf = row["FCF"]

    fundamental_score = row["FundamentalScore"]


    if (
        pd.notna(revenue_growth)
        and revenue_growth > 0
    ):

        strengths.append(
            f"Revenue is growing "
            f"({revenue_growth:.1f}% year-over-year)."
        )

    elif (
        pd.notna(revenue_growth)
        and revenue_growth < 0
    ):

        risks.append(
            f"Revenue is declining "
            f"({revenue_growth:.1f}% year-over-year)."
        )


    if (
        pd.notna(earnings_growth)
        and earnings_growth > 0
    ):

        strengths.append(
            f"Earnings are growing "
            f"({earnings_growth:.1f}% year-over-year)."
        )

    elif (
        pd.notna(earnings_growth)
        and earnings_growth < 0
    ):

        risks.append(
            f"Earnings are declining "
            f"({earnings_growth:.1f}% year-over-year)."
        )


    if (
        pd.notna(fcf)
        and fcf > 0
    ):

        strengths.append(
            "The company generated positive free cash flow."
        )

    elif (
        pd.notna(fcf)
        and fcf < 0
    ):

        risks.append(
            "The company reported negative free cash flow."
        )


    # ------------------------------------------------------
    # FUNDAMENTAL RISK
    # ------------------------------------------------------

    fundamental_risk_value = row["FundamentalRisk"]

    if fundamental_risk_value != "HEALTHY / ACCEPTABLE":

        risks.append(
            f"Fundamental assessment: "
            f"{fundamental_risk_value}."
        )


    # ------------------------------------------------------
    # GENERAL RISK
    # ------------------------------------------------------

    if row["Drawdown"] <= -50:

        risks.append(
            "The very large drawdown also means the market "
            "may be pricing in significant business or "
            "valuation risks."
        )

    if row["RSI"] > 45:

        risks.append(
            "The stock is not currently showing strongly "
            "oversold conditions."
        )


    if len(strengths) == 0:

        strengths.append(
            "The candidate achieved a strong combined "
            "score relative to the Nasdaq-100."
        )


    if len(risks) == 0:

        risks.append(
            "No major warning was identified by the "
            "current screening model."
        )


    # ------------------------------------------------------
    # OVERALL ASSESSMENT
    # ------------------------------------------------------

    final_score = row["FinalScore"]

    if final_score >= 80:

        assessment = (
            "STRONG SCREENING CANDIDATE"
        )

    elif final_score >= 70:

        assessment = (
            "GOOD SCREENING CANDIDATE"
        )

    elif final_score >= 60:

        assessment = (
            "MODERATE SCREENING CANDIDATE"
        )

    else:

        assessment = (
            "WEAK SCREENING CANDIDATE"
        )


    # ------------------------------------------------------
    # CREATE EXPLANATION
    # ------------------------------------------------------

    explanation = []

    explanation.append(
        f"{row['Ticker']} — {assessment}"
    )

    explanation.append(
        f"Final Crash Buying Score: "
        f"{final_score:.1f}/100"
    )

    explanation.append("")

    explanation.append(
        "Why selected:"
    )

    for item in strengths:

        explanation.append(
            f"• {item}"
        )


    explanation.append("")

    explanation.append(
        "Risks / things to watch:"
    )

    for item in risks:

        explanation.append(
            f"• {item}"
        )


    return "\n".join(explanation)


# ----------------------------------------------------------
# GENERATE EXPLANATIONS FOR FINAL TOP 3
# ----------------------------------------------------------

candidate_explanations = {}


for rank, (_, row) in enumerate(
    final_top3.iterrows(),
    start=1
):

    explanation = create_candidate_explanation(
        row
    )

    candidate_explanations[
        row["Ticker"]
    ] = explanation

    print()
    print("=" * 80)
    print(f"RANK #{rank}")
    print("=" * 80)

    print()
    print(explanation)


print()
print("=" * 80)
print("STAGE 8 COMPLETED")
print("=" * 80)

# ==========================================================
# STAGE 9 - EMAIL ALERT GENERATION
# ==========================================================

print()
print("=" * 80)
print("STAGE 9 - EMAIL ALERT")
print("=" * 80)

scan_date = datetime.now().strftime("%Y-%m-%d")

email_lines = []

email_lines.append("NASDAQ-100 CRASH BUYING ALERT")
email_lines.append("=" * 60)
email_lines.append("")
email_lines.append(f"Scan date: {scan_date}")
email_lines.append("")


# ----------------------------------------------------------
# USE FINAL TOP 3 FROM STAGE 7
# ----------------------------------------------------------

if len(final_top3) > 0:

    email_lines.append(
        "STRONG CRASH-BUYING OPPORTUNITY FOUND"
    )

    email_lines.append("")

    email_lines.append(
        "Top 3 candidates from the Nasdaq-100:"
    )

    email_lines.append("")


    # ------------------------------------------------------
    # CREATE EMAIL FOR EACH TOP 3 CANDIDATE
    # ------------------------------------------------------

    for rank, (_, row) in enumerate(
        final_top3.iterrows(),
        start=1
    ):

        ticker = row["Ticker"]

        email_lines.append(
            f"#{rank} {ticker}"
        )

        email_lines.append(
            f"Final Crash Buying Score: "
            f"{row['FinalScore']:.1f}/100"
        )

        email_lines.append(
            f"Technical Score: "
            f"{row['Score']:.0f}/100"
        )

        email_lines.append(
            f"Fundamental Score: "
            f"{row['FundamentalScore']:.0f}/40"
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

        email_lines.append(
            f"Revenue Growth: "
            + (
                "N/A"
                if pd.isna(row["RevenueGrowth"])
                else f"{row['RevenueGrowth']:.1f}%"
            )
        )

        email_lines.append(
            f"Earnings Growth: "
            + (
                "N/A"
                if pd.isna(row["EarningsGrowth"])
                else f"{row['EarningsGrowth']:.1f}%"
            )
        )

        email_lines.append(
            f"Fundamental Assessment: "
            f"{row['FundamentalRisk']}"
        )

        email_lines.append("")


        # --------------------------------------------------
        # WHY SELECTED
        # --------------------------------------------------

        email_lines.append(
            "Why selected:"
        )

        if row["Drawdown"] <= -30:

            email_lines.append(
                "  - Large decline from the 52-week high"
            )

        elif row["Drawdown"] <= -20:

            email_lines.append(
                "  - Significant decline from the 52-week high"
            )


        if row["RSI"] <= 30:

            email_lines.append(
                "  - Strongly oversold RSI"
            )

        elif row["RSI"] <= 40:

            email_lines.append(
                "  - RSI indicates oversold conditions"
            )


        if row["1M"] <= -15:

            email_lines.append(
                "  - Significant 1-month decline"
            )


        if row["3M"] <= -20:

            email_lines.append(
                "  - Significant 3-month decline"
            )


        if row["VolRatio"] >= 2:

            email_lines.append(
                "  - Trading volume is substantially "
                "above its 20-day average"
            )

        elif row["VolRatio"] >= 1.5:

            email_lines.append(
                "  - Trading volume is above its "
                "20-day average"
            )


        if (
            pd.notna(row["RevenueGrowth"])
            and row["RevenueGrowth"] > 0
        ):

            email_lines.append(
                "  - Revenue is still growing"
            )


        if (
            pd.notna(row["EarningsGrowth"])
            and row["EarningsGrowth"] > 0
        ):

            email_lines.append(
                "  - Earnings are still growing"
            )


        if (
            pd.notna(row["FCF"])
            and row["FCF"] > 0
        ):

            email_lines.append(
                "  - Positive free cash flow"
            )


        # --------------------------------------------------
        # RISKS
        # --------------------------------------------------

        email_lines.append("")

        email_lines.append(
            "Risks / things to watch:"
        )

        if row["FundamentalRisk"] != "HEALTHY / ACCEPTABLE":

            email_lines.append(
                f"  - {row['FundamentalRisk']}"
            )

        if (
            pd.notna(row["RevenueGrowth"])
            and row["RevenueGrowth"] < 0
        ):

            email_lines.append(
                "  - Revenue is declining"
            )

        if (
            pd.notna(row["EarningsGrowth"])
            and row["EarningsGrowth"] < 0
        ):

            email_lines.append(
                "  - Earnings are declining"
            )

        if (
            pd.notna(row["FCF"])
            and row["FCF"] < 0
        ):

            email_lines.append(
                "  - Free cash flow is negative"
            )

        if row["Drawdown"] <= -50:

            email_lines.append(
                "  - Very large drawdown may indicate "
                "significant market or business concerns"
            )


        email_lines.append("")

        email_lines.append(
            "-" * 60
        )

        email_lines.append("")


else:

    email_lines.append(
        "NO STRONG CRASH-BUYING OPPORTUNITY FOUND"
    )

    email_lines.append("")

    email_lines.append(
        "No Nasdaq-100 company produced a qualifying "
        "final crash-buying candidate today."
    )

    email_lines.append("")


# ----------------------------------------------------------
# DISCLAIMER
# ----------------------------------------------------------

email_lines.append(
    "IMPORTANT:"
)

email_lines.append(
    "This is an automated screening system and "
    "not financial advice."
)

email_lines.append(
    "A high score does not guarantee that the stock "
    "will recover."
)

email_lines.append(
    "Always perform your own research before making "
    "an investment decision."
)


# ----------------------------------------------------------
# CREATE FINAL EMAIL
# ----------------------------------------------------------

email_subject = (
    "NASDAQ-100 Crash Buying Alert - "
    + scan_date
)

email_body = "\n".join(
    email_lines
)


# ----------------------------------------------------------
# EMAIL PREVIEW
# ----------------------------------------------------------

print()
print("=" * 80)
print("EMAIL ALERT PREVIEW")
print("=" * 80)

print()

print(email_body)

print()

print("=" * 80)
print("EMAIL SUBJECT")
print("=" * 80)

print(email_subject)

print()

print("=" * 80)
print("STAGE 9 EMAIL GENERATION COMPLETED")
print("=" * 80)
