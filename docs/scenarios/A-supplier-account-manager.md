# Scenario A: Supplier Account Manager

**Theme:** Perfect Store Command Centre: from sell-out to shelf · **Team:** 01 · **Schema:** `team_01`

> **Your persona:** *Thandi manages one of the agency's largest FMCG supplier clients. Every Monday the supplier asks: "How are my
> brands selling vs the category, are we on budget, and where are we losing share?" Thandi needs answers in minutes, not a day of spreadsheets.*

Follow the sprint steps in the [attendee guide](../attendee-guide.md). This document tells you **what to build** for your persona.

---

## Business questions to answer

1. How are **my brands** performing week by week, and vs the same period last year?
2. Am I **on budget** by retailer and category this fiscal year?
3. Where am I **gaining or losing share** of category (by region, retailer or category)?
4. Which **products** are driving growth or decline?

## Data to focus on

`fact_sales_weekly`, `fact_budget_monthly`, `dim_product`, `dim_supplier`, `dim_store`, `dim_date`

---

## Sprint 1: Dashboard v1 (quick win)

Suggested visuals (pick 4–6):
- KPI counters: Sales, Units, Margin % (latest week)
- Weekly sales trend line (this year vs last year)
- Sales by retailer (bar)
- Top 10 brands by sales (table)
- Filters: Supplier, Week range, Region, Retailer

## Sprint 2: Metric views

| Metric view | Must-have measures | Stretch measures |
|---|---|---|
| `mv_sales` | Sales, Units, Margin, Margin % | YoY growth %, Avg selling price, **Share of category %** |
| `mv_budget` | Budget, Actual, Variance, Variance % | Fiscal-year-to-date (YTD) budget attainment % |

Then rebuild the dashboard on the metric views and add **Share of category %** and **Budget variance %** visuals.

## Sprint 3: Genie test questions (ask them exactly as written)

1. What were total sales last week?
2. Show weekly sales for the last 12 weeks.
3. Which are our top 5 brands?
4. What is the margin % by category this fiscal year?
5. How do sales this year compare to last year by retailer?
6. Which retailers are below budget this quarter?
7. What is the share of category for each of our brands in Gauteng?
8. Which products declined the most vs last year?
9. What was the average selling price by brand last month?
10. Which region grew fastest year to date?

## Sprint 4a: Describe these first

`fact_sales_weekly` (especially `nsv`, `gsv`, `margin`, `fy_wk`), `fact_budget_monthly`, `dim_product`, `dim_supplier`

## Sprint 4b: Genie tuning hints

- Instructions: define **sales**, the **fiscal year/quarter**, what "top" means, and what **share of category** is.
- Sample questions: 5–8 questions Thandi would ask on a Monday.
- Example SQL: share of category and YoY growth.

## Sprint 5 ideas

- **Polish:** a "Supplier scorecard" page with drill-down from category → brand → SKU.
- **App:** Tab 1 is a brand performance table, and Tab 2 has share-of-category and budget visuals.

## Demo tip

Finish with an **action**: "Brand X is losing share in Region Y with Retailer Z. Raise it in this week's supplier meeting."
