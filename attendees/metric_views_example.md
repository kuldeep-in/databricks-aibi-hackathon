# What good metric views look like

This page shows a **complete** version of the three metric views from Sprint 2: `mv_sales`, `mv_budget` and `mv_execution`.
Use it to **compare with your own**, or if you're stuck. Try building yours from the starters in the
[instructions, Appendix A](01_instructions.md#appendix-a-metric-view-starters-fill-in-the-todos) first. You'll learn far more.

**What makes these "good":**

| Good practice | Why it matters |
|---|---|
| **Business names** for every dimension and measure (`Sales`, `Region`, not `nsv`, `rgn`) | Dashboards, Genie and people see words they understand |
| A **comment** on the metric view and on every field | It explains exactly what the number means: unit, currency, rules |
| **Synonyms** ("revenue", "NSV") and **display names** | Genie finds the right measure whatever word people use |
| **Ratios defined as a ratio of totals** (`SUM(gp) / SUM(nsv)`) | Margin % stays correct at any grouping. An average of percentages doesn't |
| **Filtered measures** for "promo sales" or "this fiscal year" | The business rule is written once, not in every chart |
| **One metric view per subject** (sales, budget, shelf execution) | Each stays simple and easy to check |

Replace `<hack_catalog>` and `<your_schema>` before you run these.

> These use metric view **version 1.1**, which supports `display_name` and `synonyms`. If your workspace rejects a field, remove the
> `display_name` and `synonyms` lines: the metric view still works, it's just less friendly for Genie.

---

## 1. Sales: `mv_sales`

```sql
CREATE OR REPLACE VIEW <hack_catalog>.<your_schema>.mv_sales
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.1
comment: "Weekly sell-out (point-of-sale) KPIs. Money in ZAR excl. VAT. The fiscal year runs March to February."
source: <hack_catalog>.<your_schema>.fact_sales_weekly
joins:
  - name: store
    source: <hack_catalog>.<your_schema>.dim_store
    on: source.str_id = store.str_id
  - name: product
    source: <hack_catalog>.<your_schema>.dim_product
    on: source.sku = product.sku
  - name: cal
    source: <hack_catalog>.<your_schema>.dim_date
    on: source.wk_strt_dt = cal.dt
dimensions:
  - name: Week
    expr: source.wk_strt_dt
    comment: "Monday that starts the sales week"
  - name: Fiscal Year
    expr: cal.fy_cd
    comment: "Fiscal year code, named after the year it ends in (FY2027 = March 2026 to February 2027)"
  - name: Fiscal Quarter
    expr: cal.fy_q
    comment: "Fiscal quarter, 1 to 4 (Q1 = March to May)"
  - name: Region
    expr: store.rgn
    comment: "Sales region, for example Gauteng North or KZN Inland"
    synonyms: ["area"]
  - name: Retailer
    expr: store.rtl_grp
    comment: "Retailer group (the retail chain)"
    synonyms: ["chain", "retailer group"]
  - name: Store
    expr: store.str_nm
    comment: "Store name"
  - name: Category
    expr: product.cat
    comment: "Product category"
  - name: Brand
    expr: product.brnd
    comment: "Brand name"
measures:
  - name: Sales
    expr: SUM(source.nsv)
    comment: "Net sales value in ZAR excl. VAT, after promotional discounts. The default meaning of 'sales'."
    display_name: "Sales (ZAR)"
    synonyms: ["revenue", "net sales", "NSV"]
  - name: Units
    expr: SUM(source.qty)
    comment: "Number of units sold"
    synonyms: ["volume", "quantity"]
  - name: Margin
    expr: SUM(source.gp)
    comment: "Gross profit in ZAR (net sales minus cost of goods)"
    synonyms: ["gross profit", "GP"]
  - name: Margin %
    expr: SUM(source.gp) / NULLIF(SUM(source.nsv), 0)
    comment: "Margin as a share of net sales. A ratio of totals, so it's correct at any grouping."
    synonyms: ["gross margin %", "GP %"]
  - name: Promo Sales
    expr: SUM(source.nsv) FILTER (WHERE source.prm_flg = 'Y')
    comment: "Net sales made while the product was on promotion"
  - name: Promo Share %
    expr: SUM(source.nsv) FILTER (WHERE source.prm_flg = 'Y') / NULLIF(SUM(source.nsv), 0)
    comment: "Share of net sales made on promotion"
  - name: Sales This FY
    expr: SUM(source.nsv) FILTER (WHERE cal.fy_cd = concat('FY', CAST(year(add_months(current_date(), -2)) + 1 AS STRING)))
    comment: "Net sales in the current fiscal year, to date"
    synonyms: ["sales YTD", "year to date sales"]
  - name: Sales Last FY Same Period
    expr: SUM(source.nsv) FILTER (WHERE cal.fy_cd = concat('FY', CAST(year(add_months(current_date(), -2)) AS STRING))
                                     AND source.wk_strt_dt <= add_months(current_date(), -12))
    comment: "Net sales in the previous fiscal year, up to the same date"
  - name: YoY Growth %
    expr: >
      (SUM(source.nsv) FILTER (WHERE cal.fy_cd = concat('FY', CAST(year(add_months(current_date(), -2)) + 1 AS STRING)))
       - SUM(source.nsv) FILTER (WHERE cal.fy_cd = concat('FY', CAST(year(add_months(current_date(), -2)) AS STRING))
                                   AND source.wk_strt_dt <= add_months(current_date(), -12)))
      / NULLIF(SUM(source.nsv) FILTER (WHERE cal.fy_cd = concat('FY', CAST(year(add_months(current_date(), -2)) AS STRING))
                                         AND source.wk_strt_dt <= add_months(current_date(), -12)), 0)
    comment: "Year-to-date growth: this fiscal year to date vs the same period last fiscal year"
    synonyms: ["year on year growth", "growth %"]
$$;
```

**How the fiscal year works here:** the fiscal year starts on 1 March, so "the current fiscal year" is the one that started in the
year of the date two months ago (`year(add_months(current_date(), -2))`), and its code is that year + 1.

---

## 2. Budget: `mv_budget`

The budget table has no sales, so the source is a query that puts monthly budget and monthly actual sales side by side.

```sql
CREATE OR REPLACE VIEW <hack_catalog>.<your_schema>.mv_budget
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.1
comment: "Monthly net sales budget vs actual, by region, retailer group and category. ZAR excl. VAT."
source: |
  SELECT b.mth_strt_dt, b.rgn, b.rtl_grp, b.cat, b.bgt_nsv, a.actual_nsv
  FROM <hack_catalog>.<your_schema>.fact_budget_monthly b
  LEFT JOIN (
    SELECT CAST(trunc(f.wk_strt_dt, 'MM') AS DATE) AS mth_strt_dt, s.rgn, s.rtl_grp, p.cat, SUM(f.nsv) AS actual_nsv
    FROM <hack_catalog>.<your_schema>.fact_sales_weekly f
    JOIN <hack_catalog>.<your_schema>.dim_store s ON f.str_id = s.str_id
    JOIN <hack_catalog>.<your_schema>.dim_product p ON f.sku = p.sku
    GROUP BY ALL) a
  ON a.mth_strt_dt = b.mth_strt_dt AND a.rgn = b.rgn AND a.rtl_grp = b.rtl_grp AND a.cat = b.cat
dimensions:
  - name: Month
    expr: mth_strt_dt
    comment: "First day of the budget month"
  - name: Region
    expr: rgn
    comment: "Sales region"
  - name: Retailer
    expr: rtl_grp
    comment: "Retailer group"
  - name: Category
    expr: cat
    comment: "Product category"
measures:
  - name: Budget
    expr: SUM(bgt_nsv)
    comment: "Budgeted net sales in ZAR excl. VAT"
    synonyms: ["target", "plan"]
  - name: Actual
    expr: SUM(actual_nsv)
    comment: "Actual net sales in ZAR excl. VAT, for the same months"
    synonyms: ["actual sales"]
  - name: Variance
    expr: SUM(actual_nsv) - SUM(bgt_nsv)
    comment: "Actual minus budget in ZAR. Negative = below budget"
  - name: Variance %
    expr: (SUM(actual_nsv) - SUM(bgt_nsv)) / NULLIF(SUM(bgt_nsv), 0)
    comment: "Actual vs budget as a percentage. Negative = below budget. 'Furthest below budget' = the lowest value"
    synonyms: ["budget variance", "vs budget"]
  - name: Budget Attainment %
    expr: SUM(actual_nsv) / NULLIF(SUM(bgt_nsv), 0)
    comment: "Actual as a share of budget (100% = on budget)"
$$;
```

---

## 3. Shelf execution: `mv_execution`

```sql
CREATE OR REPLACE VIEW <hack_catalog>.<your_schema>.mv_execution
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.1
comment: "In-store execution KPIs from merchandiser visits. The on-shelf availability (OSA) target is 85%."
source: <hack_catalog>.<your_schema>.fact_store_visits
joins:
  - name: store
    source: <hack_catalog>.<your_schema>.dim_store
    on: source.str_id = store.str_id
dimensions:
  - name: Visit Date
    expr: source.vst_dt
    comment: "Date of the merchandiser visit"
  - name: Visit Week
    expr: CAST(date_trunc('week', source.vst_dt) AS DATE)
    comment: "Monday that starts the visit week (matches the sales week)"
  - name: Region
    expr: store.rgn
    comment: "Sales region"
  - name: Retailer
    expr: store.rtl_grp
    comment: "Retailer group"
  - name: Store
    expr: store.str_nm
    comment: "Store name"
measures:
  - name: Visits
    expr: COUNT(1)
    comment: "Number of merchandiser visits"
  - name: Stores Visited
    expr: COUNT(DISTINCT source.str_id)
    comment: "Number of different stores visited"
  - name: Avg OSA %
    expr: AVG(source.osa_pct)
    comment: "Average on-shelf availability, 0 to 100. Target 85."
    synonyms: ["OSA", "availability", "in-stock rate"]
  - name: Avg POG Compliance %
    expr: AVG(source.pog_comp)
    comment: "Average planogram compliance, 0 to 100"
    synonyms: ["planogram compliance", "POG"]
  - name: Avg Share of Shelf %
    expr: AVG(source.sos)
    comment: "Average share of shelf, 0 to 100"
  - name: '% Stores Below OSA Target'
    expr: COUNT(DISTINCT source.str_id) FILTER (WHERE source.osa_pct < 85) / NULLIF(COUNT(DISTINCT source.str_id), 0)
    comment: "Share of visited stores that had at least one visit with OSA below the 85% target"
$$;
```

---

## Try them

```sql
-- Which regions are below budget this fiscal year?
SELECT Region, MEASURE(`Variance %`) AS variance_pct
FROM <your_schema>.mv_budget
WHERE Month >= make_date(year(add_months(current_date(), -2)), 3, 1)
GROUP BY ALL ORDER BY variance_pct;

-- Sales, margin % and growth by region
SELECT Region, MEASURE(Sales) AS sales, MEASURE(`Margin %`) AS margin_pct, MEASURE(`YoY Growth %`) AS yoy
FROM <your_schema>.mv_sales
GROUP BY ALL ORDER BY sales DESC;

-- Shelf execution by region
SELECT Region, MEASURE(`Avg OSA %`) AS osa, MEASURE(`% Stores Below OSA Target`) AS below_target
FROM <your_schema>.mv_execution
GROUP BY ALL ORDER BY osa;
```
