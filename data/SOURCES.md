# Data sources

All figures in `steel_financials.csv` are in billion VND (rounded to 0.1), except `shares_outstanding` (millions) and `share_price_year_end` (VND).

The original report PDFs referred to below (`reports/...`) were downloaded from the listed websites. They are not included in the public repository, because they are the companies' own documents.

## HPG — Hoa Phat Group

Financial statements are from the **audited consolidated financial statements** downloaded from hoaphat.com.vn (Quan hệ cổ đông → Báo cáo tài chính). Copies are in `reports/hpg/`.

| Years | Report | Auditor |
|---|---|---|
| 2025, 2024 | `hpg_2025_audited_consolidated.pdf` (signed 24/03/2026) | — |
| 2023, 2022 | `hpg_2023_audited_consolidated.pdf` (signed 21/03/2024) | KPMG |
| 2021, 2020 | `hpg_2021_audited_consolidated.pdf` (signed 17/03/2022) | KPMG |

Each year uses the most recent report that contains it. The 2024 liabilities are shown as restated ("Trình bày lại") in the 2025 report.

Line items used (VAS codes):
- revenue = code 10, cost_of_goods_sold = 11, profit_before_tax = 50, interest_expense = 23, net_income = 60 (includes minority interests)
- depreciation = cash flow code 02 (depreciation and amortisation, including goodwill amortisation)
- cash = 110, receivables = 130, inventory = 140, total_current_assets = 100, total_assets = 270/440
- total_current_liabilities = 310, short_term_debt = 320, long_term_debt = 338, total_liabilities = 300
- retained_earnings = 421, total_equity = 400 (includes minority interests)
- cfo = cash flow code 20, capex = cash flow code 21 (shown as a positive number)
- shares_outstanding = share capital (code 411) ÷ 10,000 VND par value

Share prices are the **unadjusted** closing price on the last trading day of each year, from CafeF's price history (cafef.vn, "Giá đóng cửa"). They are unadjusted so they match the share count on the same date.

Note: HPG paid stock dividends in 2021, 2022, 2024 and 2025, so the share count rises in those years. In the Piotroski F-Score this counts as "new shares issued", even though no cash was raised. Mention this in the limitations section.

## HSG — Hoa Sen Group

**Financial year ends 30 September.** "2025" means the year 1 Oct 2024 – 30 Sep 2025, and so on.

| Years | Report | Source |
|---|---|---|
| FY2025, FY2024 | `reports/hsg/hsg_2025_audited_consolidated.pdf` (signed 26/12/2025, PwC) | hoasengroup.vn |
| FY2023, FY2022 | `reports/hsg/hsg_2023_audited_consolidated.pdf` (signed 22/12/2023, KPMG) | hoasengroup.vn |
| FY2021, FY2020 | `reports/hsg/hsg_2021_audited_consolidated.pdf` (signed 24/12/2021, KPMG) | hoasengroup.vn |

Share price is the unadjusted close on the last trading day of **September** (CafeF), to match the balance sheet date.

## NKG — Nam Kim Steel

| Years | Report | Source |
|---|---|---|
| 2025, 2024 | `reports/nkg/nkg_2025_audited_consolidated.pdf` (signed 23/03/2026, PwC) | Vietstock document library (copy of the official filing; namkimgroup.vn was unreachable) |
| 2023, 2022 | `reports/nkg/nkg_2023_audited_consolidated.pdf` (signed 20/03/2024, PwC) | Vietstock document library |
| 2021, 2020 | `reports/nkg/nkg_2021_audited_consolidated.pdf` (signed 21/03/2022) | Vietstock document library |

Share prices: unadjusted year-end close from CafeF.

## GDA — Ton Dong A

| Years | Report | Source |
|---|---|---|
| 2025, 2024 | `reports/gda/gda_2025_audited_consolidated.pdf` (signed 24/03/2026) | tondonga.com.vn |
| 2023, 2022 | `reports/gda/gda_2023_audited_consolidated.pdf` (signed 28/03/2024, EY) | tondonga.com.vn |
| 2021, 2020 | `reports/gda/gda_2021_audited_consolidated.pdf` (signed 22/03/2022) | tondonga.com.vn |

- `long_term_debt` for GDA includes convertible bonds (code 339) where they exist (2020, 2022, 2024).
- **Share prices 2020–2022 are blank**: GDA had no public trading price in those years (no history on CafeF or Vietstock), so market-based measures (original Altman Z, P/E, P/B) are missing for them. It moved from UPCoM to HOSE in November 2026.
- 2023–2025 prices are the **average price on the last trading day of the year** from Vietstock's free price history. The exact unadjusted close isn't available on the free plan, but the day's high–low range was within about 1%.

## Other notes

- NKG 2020 and HSG 2020 held small amounts of treasury shares. They're ignored in `shares_outstanding` (under 0.5% effect).
- Where a company had no long-term borrowings, `long_term_debt` is 0.
