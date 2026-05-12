# 💄 Beauty E-Commerce Sales Dataset — Project README

## Overview

This project analyzes transactional sales data from a beauty e-commerce platform, covering a **713-day** period. The cleaned dataset serves as the foundation for sales performance analysis, category insights, and trend forecasting.

---

## Dataset Summary

| Metric | Value |
|---|---|
| Total Rows | 14,611 |
| Total Columns | 43 |
| Date Range | 713 days |
| Data Retention After Cleaning | 96.4% |
| Total Revenue | $1,868,592.04 |
| Average Order Value (AOV) | $127.89 |

---

## Project Structure

```
Beauty data/
├── raw/
│   └── beauty_sales_raw.csv           # Original uncleaned dataset
├── cleaned/
│   ├── beauty_sales_cleaned.csv       # Main cleaned dataset (14,611 rows × 43 cols)
│   ├── summary_statistics.csv         # Descriptive statistics for numeric columns
│   ├── category_summary.csv           # Revenue & order breakdown by product category
│   └── monthly_trend.csv             # Aggregated monthly revenue trend
└── scripts/
    ├── 01_cleaning.py                 # Data cleaning pipeline
    └── 02_analysis.py                 # Deeper EDA & insights
```

---

## Data Cleaning Notes

- **Rows removed:** ~3.6% of original data (duplicates, nulls in critical fields, outliers)
- **Data retention:** 96.4% — high-quality source data
- **Key columns:** Order ID, Order Date, Product Category, Revenue, Quantity, Customer ID *(refer to column dictionary below)*
- All monetary values are in **USD**

---

## Key Metrics

### Revenue
- **Total Revenue:** $1,868,592.04
- **Average Order Value:** $127.89
- Revenue trends available in `monthly_trend.csv`

### Coverage
- **Date Range:** 713 days (approx. 23.5 months)
- **Granularity:** Order-level transactions

---

## Output Files

| File | Description |
|---|---|
| `beauty_sales_cleaned.csv` | Primary analysis-ready dataset |
| `summary_statistics.csv` | Mean, median, std, min/max per numeric column |
| `category_summary.csv` | Revenue, order count, and AOV by product category |
| `monthly_trend.csv` | Month-over-month revenue aggregation |

---

## Next Steps

- [ ] Review cleaned data in **Excel / Power BI**
- [ ] Run `data_cleaning.py` for deeper insights (cohort, RFM, category ranking)
- [ ] Build **Power BI dashboard** — KPIs, trend charts, category breakdown

---

## Tools Used

| Tool | Purpose |
|---|---|
| Python (pandas) | Data cleaning & aggregation |
| Power BI | Dashboard & visualization |
| Excel | Quick data review |

---

## Notes

- AOV of **$127.89** suggests a mid-to-premium product positioning
- 713-day span enables reliable **seasonality analysis** (covers ~2 annual cycles)
- Category-level data in `category_summary.csv` is ready for Power BI slicers

---

*Last updated: May 2026*
