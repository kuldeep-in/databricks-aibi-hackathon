# Scenario B: Field Operations Manager

**Theme:** Perfect Store Command Centre: from sell-out to shelf · **Team:** 02 · **Schema:** `team_02`

> **Your persona:** *Sipho runs a field team of merchandisers across several regions. He has to decide every week which stores need a
> visit, which reps need coaching, and whether poor shelf execution is costing the clients sales.*

Follow the sprint steps in the [attendee guide](../attendee-guide.md). This document tells you **what to build** for your persona.

---

## Business questions to answer

1. How good is **in-store execution**: on-shelf availability (OSA), planogram compliance and share of shelf, by region, retailer and store?
2. Which **stores** have the worst execution, and are they losing sales?
3. Which **merchandisers** perform best and worst, and does **visit frequency** make a difference?
4. Where should the team go **next week**?

## Data to focus on

`fact_store_visits`, `dim_merchandiser`, `dim_store`, `dim_date`, plus `fact_sales_weekly` to link execution to sales

---

## Sprint 1: Dashboard v1 (quick win)

Suggested visuals (pick 4–6):
- KPI counters: visits, avg OSA %, avg POG compliance %
- OSA % trend by week
- OSA % by region (bar or map, using store lat/long)
- Bottom 20 stores by OSA (table)
- Filters: Region, Retailer, Merchandiser, Week range

## Sprint 2: Metric views

| Metric view | Must-have measures | Stretch measures |
|---|---|---|
| `mv_execution` | Visits, Avg OSA %, Avg POG compliance %, Avg share of shelf % | Visits per store per month, % of stores below the 85% OSA target |
| `mv_sales` | Sales, Units | Sales YoY growth % (to compare with OSA) |

Then rebuild the dashboard on the metric views and add an **"OSA vs sales growth by region"** visual.

## Sprint 3: Genie test questions (ask them exactly as written)

1. How many store visits were done last week?
2. What is the average OSA by region this month?
3. Which 10 stores have the lowest on-shelf availability?
4. Which merchandisers have the best planogram compliance this quarter?
5. How many stores are below the OSA target?
6. What is the average visit duration by retailer?
7. Show OSA trend by week for the last 3 months.
8. Do stores with more visits have better compliance?
9. Which regions have falling OSA and falling sales?
10. Which stores were not visited in the last 4 weeks?

## Sprint 4a: Describe these first

`fact_store_visits` (especially `osa_pct`, `pog_comp`, share of shelf, duration), `dim_merchandiser`, `dim_store`

## Sprint 4b: Genie tuning hints

- Instructions: the **OSA target (85%)**, what a "visit" is, the **fiscal calendar**, and that "worst" means lowest OSA unless stated.
- SQL expressions: the filter `Below OSA target` and the measure `Visits per store`.
- Example SQL: joining visits to weekly sales by store and week.

## Sprint 5 ideas

- **AI Functions:** classify `visit_notes` (out of stock, damaged display, missing price tag, and so on) and add the results to the dashboard.
- **App:** Tab 1 is a "next week's visit list" table of the stores below target, and Tab 2 has execution visuals by region and rep.

## Demo tip

Show the money: "Stores below 85% OSA in Region Y lost Z% sales. Send the team there first."
