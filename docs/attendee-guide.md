# Perfect Store Command Centre: Attendee Guide

**Databricks Hackathon · 4 hours · AI/BI Dashboards · Metric Views · Genie · Databricks Apps**

> *You are the insights analyst at a fictional retail-execution agency. Every Monday morning the agency's FMCG clients ask three
> questions: **How did we sell?** **Are we on budget?** **What is happening on the shelf?** You have one morning to build the command
> centre that answers them: a dashboard, a trusted Genie space and a small app.*

**Everyone builds the same thing**, on their own, in their own schema. This guide tells you **what** to build in each sprint.
Facilitators will demo the **how** at the start of each sprint, so watch the demo, then build.

---

## 1. Before you start

| Item | Value |
|---|---|
| Workspace URL | `<workspace-url>` |
| Catalog | `<hack_catalog>` |
| Source data (read-only) | `<hack_catalog>.hack_14oct` |
| Your schema | `<hack_catalog>.<your_name>`: created for you by the setup notebook, named after you (for example `jane_doe`) |
| SQL warehouse ID | `<warehouse_id>` (enter it in `01_attendee_setup`; use this warehouse for your dashboard, Genie space and app) |
| Setup notebook | `<workspace-path>/01_attendee_setup` |

**Checklist:** ☐ I can log in ☐ I have the catalog name and the SQL warehouse ID

---

## 2. The business questions

1. How did we sell **last week** and **year to date**, compared with last year and with **budget**?
2. Which **regions and retailers** are driving or dragging performance?
3. Where is **poor shelf execution** (on-shelf availability, OSA) **costing sales**?
4. Which **promotions** grow sales **profitably**, and which lose money?

**Data you'll use:** `fact_sales_weekly`, `fact_budget_monthly`, `fact_store_visits`, `fact_promotions`, `dim_store`, `dim_product`, `dim_date`

---

## 3. Rules

1. Work **only in your own schema**. `hack_14oct` is read-only, and you copy from it once.
2. Start every name with your initials: dashboard `JD – …`, Genie space `JD – …`, app `jd-…`. Metric views go in your schema as `mv_…`.
3. Use the **AI help everywhere**: the Assistant, AI-generated descriptions, AI-assisted dashboard widgets, and Genie Code for the app.
4. After each improvement, **re-ask the same Genie questions** and compare the answers.
5. Stuck for more than 5 minutes? Raise a hand.

---

## 4. The day at a glance

| Time | Sprint | What you do | Done when |
|---|---|---|---|
| 0:00 – 0:15 | Kick-off | Hear the storyline and the business questions | Ready |
| 0:15 – 0:30 | **0. Your setup** | Create your own schema and copy the data into it | ✅ Tables in your schema |
| 0:30 – 1:00 | **1. Dashboard quick win** | Build a first dashboard straight on your tables | ✅ Dashboard v1 published |
| 1:00 – 1:45 | **2. Metric views** | Define your KPIs once as metric views, and rebuild the dashboard on them | ✅ Dashboard v2 on metric views |
| 1:45 – 1:55 | Break | | |
| 1:55 – 2:20 | **3. Genie quick win** | Create a Genie space and ask the 10 questions | ✅ Genie space created |
| 2:20 – 2:40 | **4a. Describe your data** | Add table and column descriptions in Unity Catalog, then re-ask the 10 questions | ✅ Tables described |
| 2:40 – 3:10 | **4b. Tune Genie** | Instructions, sample questions, SQL expressions, metric views | ✅ Genie tuned |
| 3:10 – 3:30 | **5. App** | Build a two-tab app with Genie Code: data table, then visuals | ✅ App deployed |
| 3:30 – 3:55 | Demos | 5 volunteers: 3 min demo + 1 min Q&A each | |
| 3:55 – 4:00 | Wrap-up | | |

---

## 5. What to do in each sprint

### Sprint 0: Your setup (15 min)

1. Open `01_attendee_setup`, enter the `catalog` and `warehouse_id`, leave `my_schema` blank (your schema is named after you), and click **Run all**.
   It creates **your own schema**, then **copies every table** from the read-only `hack_14oct` into it.
2. Open **Catalog Explorer → `<hack_catalog>` → your schema** and check that the tables are there.
3. Look at a few tables. Notice the **lineage** back to `hack_14oct`, the **cryptic column names**, and that there are **no descriptions**. You'll fix that later.

### Sprint 1: Dashboard quick win (30 min)

1. Create an **AI/BI Dashboard** named `<initials> – Monday Command Centre`.
2. Add your tables as datasets (the weekly sales fact table and its dimensions).
3. Use the **AI assistant** in the dashboard to build one page with 4–6 visuals:
   - KPI counters: Sales last week, Sales YTD, Budget attainment %, Avg OSA %
   - Weekly sales trend (this year vs last year)
   - Sales by region (bar or map)
   - Retailer table: sales, growth, budget variance
   - Filters: Week range, Region, Retailer, Category
4. **Publish** it. That's dashboard **v1**.

> Don't aim for perfection. Get something working quickly. Notice how much SQL or guessing each visual needs.

### Sprint 2: Metric views (45 min)

1. Create your first **metric view**, `mv_sales`, in your schema (starter in Appendix A).
2. Query it with `MEASURE()` in the SQL editor and check that the numbers look right.
3. Build all three metric views:

   | Metric view | Measures to build |
   |---|---|
   | `mv_sales` | Sales, Units, Margin, **Margin %**, YoY growth %, Promo Sales |
   | `mv_budget` | Budget, Actual, **Variance %** |
   | `mv_execution` | Visits, **Avg OSA %**, Avg POG compliance %, % of stores below the 85% OSA target |

4. Add descriptions, display names and synonyms to your measures.
5. **Switch your dashboard datasets** to the metric views. That's dashboard **v2**. Compare it with v1.
6. Add a second **"Why?" page** with a drill-down (region → retailer → store) and an "OSA vs sales growth by region" visual.

#### ⭐ Bonus: build a custom visual

If you finish early, add a **custom visual** to your dashboard: a **bullet chart of Sales vs Budget by region**, which the built-in
chart types can't draw. AI/BI dashboards render custom visuals from a **Vega-Lite** spec (*Custom Viz*). See Appendix D.

### Sprint 3: Genie quick win (25 min)

1. Create a **Genie space** named `<initials> – Monday Genie`, using your **tables** (not the metric views yet).
2. Ask these **10 questions exactly as written**:
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
3. Note which answers look wrong or unclear. You'll fix them in Sprint 4.

### Sprint 4a: Describe your data (20 min, a key capability)

1. In **Catalog Explorer**, open each of your tables and use **AI generate** for the table description, then for the column descriptions.
2. **Review every suggestion.** Correct the meanings, units (ZAR, %), grain, codes and abbreviations (Appendix B).
3. Start with the columns behind the 10 questions:
   `fact_sales_weekly` (`nsv`, `gsv`, `gp`, `qty`, `prm_flg`, `wk_strt_dt`), `fact_budget_monthly` (`bgt_nsv`, `mth_strt_dt`),
   `fact_store_visits` (`osa_pct`, `pog_comp`, `vst_dt`), `fact_promotions` (`mech`, `prm_typ`, `disc`), `dim_store` (`rgn`, `rtl_grp`, `fmt_cd`),
   `dim_date` (`fy_cd`, `fy_q`, `fy_wk`)
4. You can also bulk-edit with SQL `COMMENT ON` / `ALTER COLUMN … COMMENT`, and add tags.
5. **Re-ask the same 10 questions without changing anything else**, and compare the answers.

### Sprint 4b: Tune Genie (30 min)

Work through this list from the top. After each step, re-ask the questions that still look wrong:

1. **General instructions:** sales means net sales value (`nsv`), the **fiscal year runs March–February**, "last week" is the last complete
   week, the **OSA target is 85%**, "furthest below budget" means the lowest variance %, and currency is ZAR.
2. **Space-level refinements:** synonyms, hide columns you don't need.
3. **Sample questions:** 5–8 starter questions a client would ask on a Monday.
4. **SQL expressions:** reusable measures and filters.
5. **Joins and example SQL** for the hard questions (YoY growth, joining visits to sales by store and week).
6. **Add your three metric views** to the space, so Genie uses the governed KPIs.
7. **Trusted assets:** a UC SQL function for a parameterised question.

### Sprint 5: App (20 min)

Build a two-tab Databricks App with **Genie Code** (Appendix C):
- **Tab 1 "Data":** a filterable table from `mv_sales` (Region, Retailer, Category, Week). Do this first and deploy it.
- **Tab 2 "Insights":** KPI tiles (Sales, Margin %, YoY growth, OSA %), a weekly sales trend and sales by region.

### Demo (5 volunteers, 3 minutes each)

Tell a **before → after** story:
1. The Monday question (15 s).
2. Dashboard v1 → v2 on metric views: what changed (45 s).
3. Genie: a live question, before and after tuning (60 s).
4. The insight you found and the action to take this week (30 s). For example: *"Region Y is below budget. Its OSA dropped below 85%,
   and its stores lost sales. Promotion X drives volume but loses money. This week: send the field team to Region Y, and stop promotion X."*
5. The app (30 s).

---

## Appendix A: Metric view starter (fill in the TODOs)

> The source columns are **cryptic on purpose** (`str_id`, `sku`, `qty`, `nsv`, `gp`, `rgn` …). A metric view is where you give them
> **business names**. The joins and two examples are filled in. Work out the rest by looking at the tables in **Catalog Explorer**
> (or ask the Assistant: *"what does column gp in fact_sales_weekly contain?"*).

```sql
CREATE OR REPLACE VIEW <hack_catalog>.<your_schema>.mv_sales
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.1
comment: "Weekly sell-out KPIs"
source: <hack_catalog>.<your_schema>.fact_sales_weekly
joins:
  - name: store
    source: <hack_catalog>.<your_schema>.dim_store
    on: source.str_id = store.str_id
  - name: product
    source: <hack_catalog>.<your_schema>.dim_product
    on: source.sku = product.sku
dimensions:
  - name: Week
    expr: source.wk_strt_dt
  - name: Region
    expr: store.rgn
  # TODO: Retailer (which dim_store column holds the retailer group?)
  # TODO: Category and Brand (from dim_product)
measures:
  - name: Sales
    expr: SUM(source.nsv)          # net sales value, ZAR excl. VAT
  # TODO: Units (which column holds the units sold?)
  # TODO: Margin (gross profit in ZAR)
  # TODO: Margin %: a ratio of two sums, not an average
  # TODO: Promo Sales, using FILTER (WHERE …) on the promotion flag
$$;

SELECT Region, MEASURE(Sales) AS sales
FROM <hack_catalog>.<your_schema>.mv_sales
GROUP BY ALL ORDER BY sales DESC;
```

You can also create metric views from **Catalog Explorer** (Create → Metric view) and ask the Assistant to help with the YAML.

---

## Appendix B: Cheat-sheets

### What a good description includes

| Include | Example |
|---|---|
| Business meaning | "Net sales value after discounts and returns" |
| Unit and currency | "in ZAR, excl. VAT", "percentage 0–100" |
| Grain (table level) | "One row per store, SKU and week" |
| Codes and allowed values | "`prm_flg`: Y = on promotion, N = regular price", "`fmt_cd`: HYP = hypermarket …" |
| Abbreviations spelled out | "OSA = on-shelf availability" |
| Synonyms | "also called availability, in-stock rate" |

### Common terms

| Term | Meaning |
|---|---|
| **NSV / GSV** | Net / gross sales value |
| **OSA** | On-shelf availability: % of the expected products found on shelf during a visit |
| **POG compliance** | Planogram compliance: % of shelf matching the agreed layout |
| **Share of shelf** | The brand's share of shelf space in its category |
| **Sell-out** | Sales from the retailer to shoppers (point-of-sale data) |
| **Fiscal year (FY)** | March to February |
| **Merchandiser / rep** | A field team member who visits stores |

---

## Appendix C: App with Genie Code

Create an app named `<initials>-command-centre` (Compute → Apps → Create, with the SQL warehouse added as a resource). Open **Genie Code** and build it in two stages.

**Stage 1: Tab 1 "Data" (a table)**
> Build a Streamlit Databricks App called "<initials> Command Centre" with two tabs: "Data" and "Insights". Leave "Insights" empty for now.
> On the "Data" tab, query `<hack_catalog>.<your_schema>.mv_sales` through the SQL warehouse app resource, using `MEASURE()` for
> Sales, Units and Margin %, grouped by Region, Retailer, Category and Week. Show the result as a sortable table, with sidebar filters
> for Region, Retailer, Category and a week range. Format currency as ZAR and Margin % as a percentage. Cache the query results.

✅ Deploy, open the app URL, and check that the filters work. Then grant your app's service principal access to your schema:
`GRANT USE SCHEMA, SELECT ON SCHEMA <hack_catalog>.<your_schema> TO \`<app-sp-application-id>\`;`

**Stage 2: Tab 2 "Insights" (visuals)**
> On the "Insights" tab, add KPI tiles for Sales, Margin % and YoY growth from `mv_sales`, and OSA % from `mv_execution`. Below them, add
> a weekly sales trend line chart and a bar chart of sales by Region. Use the same sidebar filters as the "Data" tab.

✅ Changing a filter updates both tabs. To refine, use small follow-up prompts ("add a CSV download", "highlight Margin % below 20% in red").
Don't change the app's start command or port.

---

## Appendix D: ⭐ Bonus custom visual (Vega-Lite)

**Goal:** a bullet chart that shows each region's **Sales** as a bar against its **Budget** (a lighter bar with a target tick).

1. **Add a dataset** to your dashboard with one row per region and two numbers. For example, combine your metric views:
   ```sql
   SELECT s.Region AS region, s.sales, b.budget
   FROM (SELECT Region, MEASURE(Sales) AS sales FROM <your_schema>.mv_sales GROUP BY ALL) s
   JOIN (SELECT Region, MEASURE(Budget) AS budget FROM <your_schema>.mv_budget GROUP BY ALL) b USING (Region)
   ```
   (Use the dimension and measure names you gave your own metric views.)
2. Add a visualization on that dataset, then choose **Advanced → Custom Viz**.
3. Under **Fields**, add `region`, `sales` and `budget`, each with that exact **Name**.
4. Paste this spec, then adjust it:

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "data": {"name": "databricks_query"},
  "encoding": {"y": {"field": "region", "type": "nominal", "sort": "-x", "title": null}},
  "layer": [
    {"mark": {"type": "bar", "opacity": 0.3},
     "encoding": {"x": {"field": "budget", "type": "quantitative", "title": "ZAR"}}},
    {"mark": {"type": "bar", "size": 10},
     "encoding": {"x": {"field": "sales", "type": "quantitative"}}},
    {"mark": {"type": "tick", "thickness": 2, "size": 22},
     "encoding": {"x": {"field": "budget", "type": "quantitative"}}}
  ]
}
```

**Make it better:** add a tooltip with sales, budget and variance %, colour regions that are below budget, or make the chart
**cross-filter** the rest of the dashboard by adding a point-selection parameter named `databricks_mark_selection` on `region`.
Ask the Assistant to help you edit the Vega-Lite.

> Custom Viz is in **Public Preview**. If you don't see *Advanced → Custom Viz*, ask your facilitator.
