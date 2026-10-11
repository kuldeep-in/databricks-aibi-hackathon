# Scenario D: Client Executive

**Theme:** Perfect Store Command Centre: from sell-out to shelf · **Team:** 04 · **Schema:** `team_04`

> **Your persona:** *Johan is the agency's client executive. On Monday morning he has 10 minutes before the client call. He wants one
> page that shows the business at a glance (sales, budget, execution), with drill-downs when the client asks "why?".*

Follow the sprint steps in the [attendee guide](../attendee-guide.md). This document tells you **what to build** for your persona.

---

## Business questions to answer

1. How did we do **last week** and **year to date**, vs last year and vs budget?
2. Which **regions and retailers** are driving or dragging performance?
3. Is **in-store execution** (OSA) healthy where sales are weak?
4. What are the **three things** to raise on the client call?

## Data to focus on

`fact_sales_weekly`, `fact_budget_monthly`, `fact_store_visits`, `dim_store`, `dim_product`, `dim_date`

---

## Sprint 1: Dashboard v1 (quick win)

Suggested visuals (pick 4–6). Aim for **one executive page**:
- KPI counters: Sales last week, Sales YTD, Budget attainment %, Avg OSA %
- Weekly sales trend (this year vs last year)
- Sales by region (bar or map)
- Retailer table: sales, growth, budget variance
- Filters: Week range, Region, Retailer, Category

## Sprint 2: Metric views

| Metric view | Must-have measures | Stretch measures |
|---|---|---|
| `mv_sales` | Sales, Units, Margin %, YoY growth % | YTD sales, last week vs prior week % |
| `mv_budget` | Budget, Actual, Variance % | YTD budget attainment % |
| `mv_execution` | Avg OSA % | % of stores below the OSA target |

Then rebuild the dashboard on the metric views, add a second **"Why?" drill-down page** (region → retailer → store), and check
that every KPI uses a metric view measure.

## Sprint 3: Genie test questions (ask them exactly as written)

1. How did sales last week compare to the same week last year?
2. What are year-to-date sales vs budget?
3. Which region is furthest below budget?
4. Which retailer grew the most this quarter?
5. What is the average OSA in the region with the weakest sales growth?
6. Show sales, budget and variance by retailer for this fiscal year.
7. What were the top 3 categories last month?
8. Which week had the highest sales this year?
9. How many stores are below the OSA target in the worst-performing region?
10. Summarise performance last week in three bullet points.

## Sprint 4a: Describe these first

`fact_sales_weekly`, `fact_budget_monthly`, `dim_date` (fiscal columns such as `fy_wk`), `dim_store`

## Sprint 4b: Genie tuning hints

- Instructions: the **fiscal year (March–February)**, **YTD**, "last week" (the last complete week), "furthest below budget" (by variance %), and the format for summaries.
- Sample questions: the Monday-morning questions Johan always asks.
- Metric views: add all three, so Genie uses the governed KPIs.

## Sprint 5 ideas

- **Polish:** schedule the dashboard as a **Monday 07:00 email** subscription, and embed Genie in the dashboard for "why?" questions.
- **App:** Tab 1 is a retailer/region performance table, and Tab 2 has the executive KPI tiles and trend charts.

## Demo tip

Role-play the client call: the client asks "why is Region Y down?", and you answer live with the drill-down and then Genie.
