# Scenario C: Trade Marketing Manager

**Theme:** Perfect Store Command Centre: from sell-out to shelf · **Team:** 03 · **Schema:** `team_03`

> **Your persona:** *Lerato plans promotions with the clients and retailers. Promotions cost a lot. She needs to prove which ones
> actually grow sales **profitably**, and which ones only move volume at a loss.*

Follow the sprint steps in the [attendee guide](../attendee-guide.md). This document tells you **what to build** for your persona.

---

## Business questions to answer

1. How much of our sales come **on promotion**, and is that share growing?
2. What **uplift** does each promotion mechanic (for example multi-buy, % off, bundle) deliver?
3. Which promotions are **profitable**, and which hurt margin?
4. Which categories, retailers and regions respond best to promotions?

## Data to focus on

`fact_promotions`, `fact_sales_weekly` (promo flag), `dim_product`, `dim_store`, `dim_date`

---

## Sprint 1: Dashboard v1 (quick win)

Suggested visuals (pick 4–6):
- KPI counters: promo sales, promo share of sales %, number of active promotions
- Weekly sales with promo weeks highlighted
- Sales and margin % by promotion mechanic (bar)
- Top/bottom 10 promotions (table)
- Filters: Mechanic, Category, Retailer, Week range

## Sprint 2: Metric views

| Metric view | Must-have measures | Stretch measures |
|---|---|---|
| `mv_sales` | Sales, Units, Margin %, **Promo sales**, **Promo share %** | Margin % on promo vs off promo |
| `mv_promo` (on promotions + sales) | Promo count, Avg discount % | **Uplift %** vs a baseline (non-promo weeks), Incremental margin |

Then rebuild the dashboard on the metric views and add an **"uplift vs margin by mechanic"** visual (a scatter chart works well).

## Sprint 3: Genie test questions (ask them exactly as written)

1. What share of sales was on promotion last quarter?
2. Which promotion mechanic had the highest sales?
3. What is the average discount by mechanic?
4. Which promotions had negative margin?
5. Show promo sales vs non-promo sales by week for the last 6 months.
6. Which category gets the most promotions?
7. What was the sales uplift of multi-buy promotions?
8. Which retailer has the highest promo share of sales?
9. What is margin % on promotion vs off promotion by category?
10. List the top 10 promotions this fiscal year.

## Sprint 4a: Describe these first

`fact_promotions` (mechanic, discount %, start/end dates), `fact_sales_weekly` (`promo_flag`, `nsv`, `margin`), `dim_product`

## Sprint 4b: Genie tuning hints

- Instructions: define **uplift** (and its baseline), **"top" promotions** (by sales or uplift?), **profitable**, and the **fiscal year**.
- SQL expressions: the measure `Promo share %` and the filter `On promotion`.
- Example SQL: an uplift calculation comparing promo weeks with the average of non-promo weeks.

## Sprint 5 ideas

- **Polish:** a "Promo post-evaluation" page with drill-down by promotion.
- **App:** Tab 1 is a promotion performance table, and Tab 2 has uplift vs margin visuals by mechanic.

## Demo tip

Finish with a recommendation: "Stop mechanic X. It drives volume but destroys margin. Move the budget to mechanic Y."
