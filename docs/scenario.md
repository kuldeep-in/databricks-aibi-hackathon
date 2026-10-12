# The scenario: Monday Command Centre

**Theme:** Perfect Store Command Centre: from sell-out to shelf · **Schema:** your own schema (created by `01_attendee_setup`)

> *You are the insights analyst at a fictional retail-execution agency. Every Monday morning the agency's FMCG clients ask three
> questions: **How did we sell?** **Are we on budget?** **What is happening on the shelf?** You have one morning to build the command
> centre that answers them: a dashboard, a trusted Genie space and a small app.*

Everyone builds the same thing. Follow the sprint steps in the [attendee guide](attendee-guide.md). This page tells you **what** to build.

---

## Business questions to answer

1. How did we sell **last week** and **year to date**, compared with last year and with **budget**?
2. Which **regions and retailers** are driving or dragging performance?
3. Where is **poor shelf execution** (on-shelf availability, OSA) **costing sales**?
4. Which **promotions** grow sales **profitably**, and which lose money?

## Data you'll use

`fact_sales_weekly`, `fact_budget_monthly`, `fact_store_visits`, `fact_promotions`, `dim_store`, `dim_product`, `dim_date`

---

## Sprint 1: Dashboard v1 (quick win)

Build one page with 4–6 visuals:
- KPI counters: Sales last week, Sales YTD, Budget attainment %, Avg OSA %
- Weekly sales trend (this year vs last year)
- Sales by region (bar or map)
- Retailer table: sales, growth, budget variance
- Filters: Week range, Region, Retailer, Category

## Sprint 2: Metric views

| Metric view | Measures to build |
|---|---|
| `mv_sales` | Sales, Units, Margin, **Margin %**, YoY growth %, Promo Sales |
| `mv_budget` | Budget, Actual, **Variance %** |
| `mv_execution` | Visits, **Avg OSA %**, Avg POG compliance %, % of stores below the 85% OSA target |

Then rebuild the dashboard on the metric views (dashboard v2), and add a second **"Why?" page** with a drill-down
(region → retailer → store) and an "OSA vs sales growth by region" visual.

## Sprint 3: Genie questions (ask them exactly as written)

1. What were total sales last week?
2. How did sales last week compare to the same week last year?
3. What are year-to-date sales vs budget?
4. Which region is furthest below budget?
5. What is the average OSA by region this month?
6. How many stores are below the OSA target?
7. Which regions have falling OSA and falling sales?
8. Which promotion mechanic has negative margin?
9. What is the margin % by category this fiscal year?
10. Which stores were not visited in the last 4 weeks?

Ask them again after describing the data (Sprint 4a) and after tuning (Sprint 4b), and compare the answers.

## Sprint 4a: Describe these first

`fact_sales_weekly` (`nsv`, `gsv`, `gp`, `qty`, `prm_flg`, `wk_strt_dt`), `fact_budget_monthly` (`bgt_nsv`, `mth_strt_dt`),
`fact_store_visits` (`osa_pct`, `pog_comp`, `vst_dt`), `fact_promotions` (`mech`, `prm_typ`, `disc`), `dim_store` (`rgn`, `rtl_grp`, `fmt_cd`),
`dim_date` (`fy_cd`, `fy_q`, `fy_wk`)

## Sprint 4b: Genie tuning hints

- Instructions: **sales** means net sales value (`nsv`), the **fiscal year runs March–February**, "last week" is the last complete week,
  the **OSA target is 85%**, and "furthest below budget" means the lowest variance %.
- Add your three **metric views** to the space, so Genie uses the governed KPIs.
- Example SQL for the hard ones: YoY growth, and joining visits to sales by store and week.

## Sprint 5: App (two tabs, built with Genie Code)

- **Tab 1 "Data":** a filterable table from `mv_sales` (Region, Retailer, Category, Week).
- **Tab 2 "Insights":** KPI tiles (Sales, Margin %, YoY growth, OSA %), a weekly sales trend and sales by region.

The Genie Code prompts are in the attendee guide, Appendix C.

## Demo tip

Tell the Monday story: *"Region Y is below budget. Its OSA dropped below 85%, and the stores there lost Z% sales. Promotion X drives
volume but loses money. This week: send the field team to Region Y, and stop promotion X."*
