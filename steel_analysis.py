"""
Financial health analysis for a peer group of companies (built for Vietnamese steel producers).

Every formula is written out in plain pandas so it can be read, checked and explained.

Units expected in the data file (see README.md):
    - All money amounts in billion VND (ty dong)
    - shares_outstanding in millions of shares
    - share_price_year_end in VND per share
    - capex as a positive number (cash spent)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "revenue",
    "cost_of_goods_sold",
    "profit_before_tax",
    "interest_expense",
    "net_income",
    "depreciation",
    "cash",
    "receivables",
    "inventory",
    "total_current_assets",
    "total_assets",
    "total_current_liabilities",
    "short_term_debt",
    "long_term_debt",
    "total_liabilities",
    "retained_earnings",
    "total_equity",
    "shares_outstanding",
    "cfo",
    "capex",
    "share_price_year_end",
]


# ---------------------------------------------------------------------------
# Loading data
# ---------------------------------------------------------------------------


def load_financials(path: str) -> pd.DataFrame:
    """Read the data file and return a table indexed by (ticker, year)."""
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()

    missing = [c for c in ["ticker", "year", *REQUIRED_COLUMNS] if c not in df.columns]
    if missing:
        raise ValueError(f"These columns are missing from {path}: {missing}")

    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    df["year"] = df["year"].astype(int)

    value_columns = [c for c in df.columns if c not in ("ticker", "year")]
    for column in value_columns:
        # Accept numbers typed with thousands separators, e.g. "142,770".
        df[column] = pd.to_numeric(
            df[column].astype(str).str.replace(",", "").str.strip(), errors="coerce"
        )

    return df.set_index(["ticker", "year"]).sort_index()


def report_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Count how many required values are still empty for each company and year."""
    missing = df[REQUIRED_COLUMNS].isna().sum(axis=1).unstack("year")
    return missing.rename_axis(index="ticker", columns="year")


def make_demo_data(seed: int = 7) -> pd.DataFrame:
    """
    Create FICTIONAL demo data so the notebook runs before you have entered real numbers.

    The three companies (DEMO_A, DEMO_B, DEMO_C) are invented. They follow a steel-like
    cycle (boom in 2021, slump in 2022-2023) with different amounts of debt.
    Never present these numbers as real results.
    """
    rng = np.random.default_rng(seed)
    demand = {2018: 0.95, 2019: 1.0, 2020: 1.05, 2021: 1.6, 2022: 1.3, 2023: 1.0, 2024: 1.15}
    spread = {2018: 0.11, 2019: 0.10, 2020: 0.13, 2021: 0.24, 2022: 0.07, 2023: 0.05, 2024: 0.09}
    price_to_book = {2018: 1.2, 2019: 1.1, 2020: 1.6, 2021: 2.2, 2022: 0.9, 2023: 1.2, 2024: 1.3}
    # name: (base revenue, margin strength, debt-to-assets)
    companies = {"DEMO_A": (80000, 1.0, 0.18), "DEMO_B": (35000, 0.7, 0.32), "DEMO_C": (20000, 0.55, 0.45)}

    rows = []
    for ticker, (base_revenue, margin_strength, debt_ratio) in companies.items():
        retained = base_revenue * 0.08
        shares = base_revenue / 12
        for year, cycle in demand.items():
            revenue = base_revenue * cycle * rng.uniform(0.95, 1.05)
            gross_margin = spread[year] * margin_strength + 0.03
            cogs = revenue * (1 - gross_margin)
            selling_admin = revenue * 0.035
            depreciation = revenue * 0.03
            total_assets = revenue * rng.uniform(1.0, 1.2)
            debt = total_assets * debt_ratio
            interest = debt * 0.075
            profit_before_tax = revenue - cogs - selling_admin - interest
            net_income = profit_before_tax * 0.8 if profit_before_tax > 0 else profit_before_tax
            total_liabilities = debt + total_assets * 0.22
            total_equity = total_assets - total_liabilities
            retained += net_income * 0.6
            current_assets = total_assets * 0.55
            if ticker == "DEMO_C" and year == 2022:
                shares *= 1.15  # a share issue, to show the Piotroski dilution signal
            book_per_share = total_equity / shares * 1000
            rows.append(
                {
                    "ticker": ticker,
                    "year": year,
                    "revenue": revenue,
                    "cost_of_goods_sold": cogs,
                    "profit_before_tax": profit_before_tax,
                    "interest_expense": interest,
                    "net_income": net_income,
                    "depreciation": depreciation,
                    "cash": current_assets * 0.15,
                    "receivables": current_assets * 0.20,
                    "inventory": current_assets * rng.uniform(0.45, 0.6),
                    "total_current_assets": current_assets,
                    "total_assets": total_assets,
                    "total_current_liabilities": total_assets * 0.18 + debt * 0.6,
                    "short_term_debt": debt * 0.6,
                    "long_term_debt": debt * 0.4,
                    "total_liabilities": total_liabilities,
                    "retained_earnings": min(retained, total_equity * 0.6),
                    "total_equity": total_equity,
                    "shares_outstanding": shares,
                    "cfo": net_income + depreciation + rng.normal(0, revenue * 0.03),
                    "capex": revenue * rng.uniform(0.03, 0.08),
                    "share_price_year_end": book_per_share * price_to_book[year],
                }
            )

    return pd.DataFrame(rows).set_index(["ticker", "year"]).round(0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Divide, returning NaN instead of infinity when the denominator is zero."""
    return numerator / denominator.where(denominator != 0)


def _previous(df: pd.DataFrame, column: str | pd.Series) -> pd.Series:
    """The same company's value one year earlier."""
    series = df[column] if isinstance(column, str) else column
    return series.groupby(level="ticker").shift(1)


def _flag(condition: pd.Series, *inputs: pd.Series) -> pd.Series:
    """1 if the condition holds, 0 if not, NaN if any input needed for it is missing."""
    available = pd.concat(inputs, axis=1).notna().all(axis=1)
    return condition.astype(float).where(available)


def ebit(df: pd.DataFrame) -> pd.Series:
    """EBIT = profit before tax + interest expense (works for Vietnamese VAS statements)."""
    return df["profit_before_tax"] + df["interest_expense"]


def market_cap(df: pd.DataFrame) -> pd.Series:
    """Market capitalisation in billion VND (price in VND x shares in millions / 1,000)."""
    return df["share_price_year_end"] * df["shares_outstanding"] / 1000


# ---------------------------------------------------------------------------
# Ratios
# ---------------------------------------------------------------------------


def compute_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Profitability, liquidity, solvency, efficiency and cash flow ratios per company-year."""
    r = pd.DataFrame(index=df.index)
    operating_profit = ebit(df)
    ebitda = operating_profit + df["depreciation"]
    total_debt = df["short_term_debt"] + df["long_term_debt"]
    previous_revenue = _previous(df, "revenue")

    # Growth and profitability
    r["Revenue growth"] = _div(df["revenue"] - previous_revenue, previous_revenue.abs())
    r["Gross margin"] = _div(df["revenue"] - df["cost_of_goods_sold"], df["revenue"])
    r["EBIT margin"] = _div(operating_profit, df["revenue"])
    r["Net margin"] = _div(df["net_income"], df["revenue"])
    r["ROA"] = _div(df["net_income"], df["total_assets"])
    r["ROE"] = _div(df["net_income"], df["total_equity"])

    # Liquidity: can the company pay its bills over the next year?
    r["Current ratio"] = _div(df["total_current_assets"], df["total_current_liabilities"])
    r["Quick ratio"] = _div(
        df["total_current_assets"] - df["inventory"], df["total_current_liabilities"]
    )
    r["Cash ratio"] = _div(df["cash"], df["total_current_liabilities"])

    # Solvency: how much debt, and can it be serviced?
    r["Debt to equity"] = _div(total_debt, df["total_equity"])
    r["Liabilities to assets"] = _div(df["total_liabilities"], df["total_assets"])
    r["Net debt to EBITDA"] = _div(total_debt - df["cash"], ebitda)
    r["Interest coverage"] = _div(operating_profit, df["interest_expense"])

    # Efficiency: steel is inventory-heavy, so inventory days matter a lot
    r["Asset turnover"] = _div(df["revenue"], df["total_assets"])
    r["Inventory days"] = _div(df["inventory"], df["cost_of_goods_sold"]) * 365
    r["Receivable days"] = _div(df["receivables"], df["revenue"]) * 365

    # Cash flow quality
    r["Free cash flow"] = df["cfo"] - df["capex"]
    r["CFO to net income"] = _div(df["cfo"], df["net_income"])

    # Valuation (needs share prices)
    r["P/E"] = _div(market_cap(df), df["net_income"].where(df["net_income"] > 0))
    r["P/B"] = _div(market_cap(df), df["total_equity"])

    return r


# ---------------------------------------------------------------------------
# Altman Z-Score
# ---------------------------------------------------------------------------

ALTMAN_ORIGINAL_ZONES = {"distress": 1.81, "safe": 2.99}
ALTMAN_EM_ZONES = {"distress": 4.35, "safe": 5.85}


def altman_z(df: pd.DataFrame) -> pd.DataFrame:
    """
    Two versions of Altman's bankruptcy-risk score.

    Original Z (1968, US listed manufacturers):
        Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
        safe > 2.99, grey zone 1.81-2.99, distress < 1.81

    Emerging-market Z''-score (Altman, 1995/2005):
        Z'' = 3.25 + 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4(book)
        safe > 5.85, grey zone 4.35-5.85, distress < 4.35

    X1 = working capital / total assets
    X2 = retained earnings / total assets
    X3 = EBIT / total assets
    X4 = market value of equity / total liabilities (book equity in the EM version)
    X5 = revenue / total assets
    """
    total_assets = df["total_assets"]
    x1 = _div(df["total_current_assets"] - df["total_current_liabilities"], total_assets)
    x2 = _div(df["retained_earnings"], total_assets)
    x3 = _div(ebit(df), total_assets)
    x4_market = _div(market_cap(df), df["total_liabilities"])
    x4_book = _div(df["total_equity"], df["total_liabilities"])
    x5 = _div(df["revenue"], total_assets)

    out = pd.DataFrame(index=df.index)
    out["X1 working capital / TA"] = x1
    out["X2 retained earnings / TA"] = x2
    out["X3 EBIT / TA"] = x3
    out["X4 market equity / TL"] = x4_market
    out["X4 book equity / TL"] = x4_book
    out["X5 revenue / TA"] = x5
    out["Altman Z (original)"] = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4_market + 1.0 * x5
    out["Altman Z'' (emerging markets)"] = 3.25 + 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4_book
    out["Zone (original)"] = out["Altman Z (original)"].apply(_zone, zones=ALTMAN_ORIGINAL_ZONES)
    out["Zone (EM)"] = out["Altman Z'' (emerging markets)"].apply(_zone, zones=ALTMAN_EM_ZONES)
    return out


def _zone(value: float, zones: dict) -> str:
    if pd.isna(value):
        return "n/a"
    if value < zones["distress"]:
        return "Distress"
    if value > zones["safe"]:
        return "Safe"
    return "Grey"


# ---------------------------------------------------------------------------
# Piotroski F-Score
# ---------------------------------------------------------------------------


def piotroski(df: pd.DataFrame) -> pd.DataFrame:
    """
    Piotroski F-Score (2000): nine yes/no signals of improving financial strength, 0-9.

    For simplicity this uses year-end total assets; the original paper uses
    beginning-of-year assets. Each signal needs the previous year, so the first
    year in the data has no score.
    """
    total_debt_lt = df["long_term_debt"]
    roa = _div(df["net_income"], df["total_assets"])
    leverage = _div(total_debt_lt, df["total_assets"])
    current_ratio = _div(df["total_current_assets"], df["total_current_liabilities"])
    gross_margin = _div(df["revenue"] - df["cost_of_goods_sold"], df["revenue"])
    asset_turnover = _div(df["revenue"], df["total_assets"])

    prev_roa = _previous(df, roa)
    prev_leverage = _previous(df, leverage)
    prev_current_ratio = _previous(df, current_ratio)
    prev_shares = _previous(df, "shares_outstanding")
    prev_gross_margin = _previous(df, gross_margin)
    prev_asset_turnover = _previous(df, asset_turnover)

    s = pd.DataFrame(index=df.index)
    # Profitability
    s["1 ROA > 0"] = _flag(roa > 0, roa)
    s["2 CFO > 0"] = _flag(df["cfo"] > 0, df["cfo"])
    s["3 ROA improved"] = _flag(roa > prev_roa, roa, prev_roa)
    s["4 CFO > net income"] = _flag(df["cfo"] > df["net_income"], df["cfo"], df["net_income"])
    # Leverage, liquidity and funding
    s["5 Long-term debt ratio fell"] = _flag(leverage < prev_leverage, leverage, prev_leverage)
    s["6 Current ratio improved"] = _flag(
        current_ratio > prev_current_ratio, current_ratio, prev_current_ratio
    )
    s["7 No new shares issued"] = _flag(
        df["shares_outstanding"] <= prev_shares, df["shares_outstanding"], prev_shares
    )
    # Operating efficiency
    s["8 Gross margin improved"] = _flag(
        gross_margin > prev_gross_margin, gross_margin, prev_gross_margin
    )
    s["9 Asset turnover improved"] = _flag(
        asset_turnover > prev_asset_turnover, asset_turnover, prev_asset_turnover
    )
    s["F-Score"] = s.sum(axis=1, min_count=9)
    return s


# ---------------------------------------------------------------------------
# Presentation
# ---------------------------------------------------------------------------


def by_year(table: pd.DataFrame, metric: str) -> pd.DataFrame:
    """One metric as a table with companies as rows and years as columns."""
    return table[metric].unstack("year")


def snapshot(year: int, *tables: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    """Selected metrics for every company in one year, side by side."""
    combined = pd.concat(tables, axis=1)
    return combined.xs(year, level="year")[metrics].T


COLUMN_LABELS = {
    "ticker": "Company",
    "year": "Year",
    "cfo": "Operating cash flow",
    "capex": "Capital expenditure",
    "shares_outstanding": "Shares (million)",
    "share_price_year_end": "Year-end share price (VND)",
}

COMPANY_NAMES = {
    "HPG": "Hoa Phat Group",
    "HSG": "Hoa Sen Group",
    "NKG": "Nam Kim Steel",
    "GDA": "Ton Dong A",
}

# "Booktabs" tables, as used in academic journals: three horizontal rules, no shading.
TABLE_STYLES = [
    {"selector": "", "props": "border-collapse: collapse; font-size: 13px; font-family: inherit; "
                              "border-top: 1.5px solid #222; border-bottom: 1.5px solid #222; margin: 0.5em 0 1.5em;"},
    {"selector": "th", "props": "font-weight: normal; text-align: right; padding: 5px 12px; "
                                "border-bottom: 0.75px solid #222; white-space: nowrap; background: none;"},
    {"selector": "td", "props": "text-align: right; padding: 3px 12px; white-space: nowrap; "
                                "border: none; background: none;"},
    {"selector": "th:first-child, td:first-child", "props": "text-align: left; padding-left: 0;"},
    {"selector": "caption", "props": "caption-side: top; text-align: left; font-size: 13px; "
                                     "padding-bottom: 6px; color: #222;"},
]

REPORT_COLORS = ["#1f3b5c", "#8c2d19", "#4d7c4a", "#b08a2e"]


def use_report_style() -> None:
    """Academic chart style: serif font, muted colours, a different marker per company."""
    import matplotlib.pyplot as plt
    from cycler import cycler

    plt.rcParams.update({
        "figure.figsize": (8, 4),
        "figure.dpi": 110,
        "font.family": "serif",
        "font.serif": ["Georgia", "Times New Roman", "DejaVu Serif"],
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.titleweight": "normal",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#444444",
        "axes.prop_cycle": cycler(color=REPORT_COLORS) + cycler(marker=["o", "s", "^", "D"]),
        "lines.linewidth": 1.6,
        "lines.markersize": 5,
        "legend.frameon": False,
        "grid.color": "#cccccc",
        "grid.linestyle": ":",
    })


def _label(name) -> str:
    """Readable column heading: 'total_current_assets' -> 'Total current assets'."""
    name = str(name)
    if name in COLUMN_LABELS:
        return COLUMN_LABELS[name]
    return name.replace("_", " ")[:1].upper() + name.replace("_", " ")[1:]


def show(
    table: pd.DataFrame,
    title: str | None = None,
    percent=False,
    row_label: str = "Metric",
    decimals: int = 2,
):
    """
    Display a table with one clean header row, readable column names and formatted numbers.

    percent: True formats every number as a percentage; a list formats only the
    rows or columns with those labels as percentages.
    """
    flat = table.copy()
    flat.columns.name = None
    if flat.index.names == [None]:
        flat.index = flat.index.map(lambda v: _label(v) if isinstance(v, str) else v)
        flat.index.name = row_label
    flat = flat.reset_index()
    flat.columns = [_label(column) for column in flat.columns]
    first = flat.columns[0]

    def is_percent(row_name, column_name) -> bool:
        if percent is True:
            return True
        return bool(percent) and (row_name in percent or column_name in percent)

    def fmt(value, row_name, column_name):
        if isinstance(value, str):
            return value
        if pd.isna(value):
            return "–"
        if isinstance(value, (int, np.integer)) or column_name == "Year" or "F-Score" in (str(row_name), column_name):
            return str(int(value))
        if is_percent(row_name, column_name):
            return f"{value:.1%}"
        return f"{value:,.{decimals}f}"

    text = flat.astype(object).copy()
    for i, row in flat.iterrows():
        for column in flat.columns:
            text.at[i, column] = fmt(row[column], row[first], column)
    styled = text.style.hide(axis="index").set_table_styles(TABLE_STYLES)
    text_columns = [
        c for c in flat.columns[1:]
        if flat[c].dropna().map(lambda v: isinstance(v, str)).all() and flat[c].notna().any()
    ]
    if text_columns:
        left = [{"selector": "th, td", "props": "text-align: left;"}]
        styled = styled.set_table_styles({c: left for c in text_columns}, overwrite=False)
    return styled.set_caption(title) if title else styled


def plot_metric(
    table: pd.DataFrame,
    metric: str,
    title: str | None = None,
    percent: bool = False,
    zones: dict | None = None,
    ax=None,
):
    """Line chart of one metric over time, one line per company."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    data = table[metric].unstack("ticker").dropna(how="all")
    if data.empty:
        print(f"No data yet for '{metric}'. Fill in the data file first.")
        return None

    from matplotlib.transforms import blended_transform_factory

    if ax is None:
        _, ax = plt.subplots(figsize=(8, 4))
    data.plot(ax=ax, zorder=3)

    if zones:
        safe, distress = zones["safe"], zones["distress"]
        green, red = "#4d7c4a", "#8c2d19"
        low = min(data.min().min(), distress)
        high = max(data.max().max(), safe)
        pad = (high - low) * 0.12
        ax.set_ylim(low - pad, high + pad)
        bottom, top = ax.get_ylim()

        # Shaded zones: distress below the lower line, safe above the upper line
        ax.axhspan(bottom, distress, color=red, alpha=0.07, linewidth=0, zorder=0)
        ax.axhspan(safe, top, color=green, alpha=0.07, linewidth=0, zorder=0)
        ax.axhline(safe, linestyle="--", color=green, linewidth=1, zorder=1)
        ax.axhline(distress, linestyle="--", color=red, linewidth=1, zorder=1)

        # Labels with the exact cut-off values, just outside the right edge of the plot
        right = blended_transform_factory(ax.transAxes, ax.transData)
        ax.text(1.01, safe, f"Safe line\n{safe:.2f}", transform=right, color=green,
                va="center", ha="left", fontsize=8, linespacing=1.2)
        ax.text(1.01, distress, f"Distress line\n{distress:.2f}", transform=right, color=red,
                va="center", ha="left", fontsize=8, linespacing=1.2)
        ax.text(1.01, (safe + distress) / 2, "Grey zone", transform=right, color="#777777",
                va="center", ha="left", fontsize=8, style="italic")

    if percent:
        ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_title(title or metric, pad=10)
    ax.set_xlabel("")
    ax.set_xticks(list(data.index))
    ax.tick_params(axis="both", labelsize=9, length=3)
    ax.grid(axis="y", alpha=0.6)
    ax.grid(axis="x", visible=False)
    ax.legend(
        [f"{t} ({COMPANY_NAMES.get(t, t)})" for t in data.columns],
        loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=len(data.columns),
        fontsize=8.5, handlelength=2.2, columnspacing=1.6,
    )
    return ax
