# Perfect Store Command Centre: Attendee Guide

**Databricks Hackathon · 4 hours · AI/BI Dashboards · Metric Views · Genie · Databricks Apps**

> *You are the insights analyst at a fictional retail-execution agency. Every Monday morning the agency's FMCG clients ask three
> questions: **How did we sell?** **Are we on budget?** **What is happening on the shelf?** You have one morning to build the command
> centre that answers them: a dashboard, a trusted Genie space and a small app.*

**Everyone builds the same thing**, on their own, in their own schema. This guide walks you through every sprint step by step.
At the start of each sprint a facilitator gives a short demo. Watch it, then come back here and build.

---

## Contents

1. [Before you start](#1-before-you-start)
2. [How the day works](#2-how-the-day-works)
3. [The business questions and the data](#3-the-business-questions-and-the-data)
4. [Rules](#4-rules)
5. [The day at a glance](#5-the-day-at-a-glance)
6. [Sprint 0: Your setup](#sprint-0-your-setup-15-min)
7. [Sprint 1: Dashboard quick win](#sprint-1-dashboard-quick-win-30-min)
8. [Sprint 2: Metric views](#sprint-2-metric-views-45-min)
9. [Sprint 3: Genie quick win](#sprint-3-genie-quick-win-25-min)
10. [Sprint 4a: Describe your data](#sprint-4a-describe-your-data-20-min)
11. [Sprint 4b: Tune Genie](#sprint-4b-tune-genie-30-min)
12. [Sprint 5: App](#sprint-5-app-20-min)
13. [Demo](#demo-5-volunteers-3-minutes-each)
14. [Troubleshooting](#troubleshooting)
15. Appendices: [A. Metric view starter](#appendix-a-metric-view-starter-fill-in-the-todos) · [B. Cheat-sheets](#appendix-b-cheat-sheets) ·
    [C. App prompts](#appendix-c-app-with-genie-code) · [D. Bonus custom visual](#appendix-d--bonus-custom-visual-vega-lite)

---

## 1. Before you start

Your facilitator gives you these values. Write them down, because you'll need them all day.

| Item | Value |
|---|---|
| Workspace URL | `<workspace-url>` |
| Catalog | `<hack_catalog>` |
| Source data (read-only) | `<hack_catalog>.hack_14oct` |
| Your schema | `<hack_catalog>.<your_name>`: created for you by the setup notebook, named after you (for example `jane_doe`) |
| SQL warehouse ID | `<warehouse_id>`: you enter it in the setup notebook, and use this warehouse for your dashboard, Genie space and app |
| Setup notebook | `attendees/01_attendee_setup` (in the hackathon folder in the workspace) |

**Checklist before Sprint 0:**
- ☐ I can log in to the workspace
- ☐ I have the catalog name and the SQL warehouse ID
- ☐ I can open the hackathon folder and see `attendees/01_attendee_setup`

---

## 2. How the day works

Every part of the day follows the same rhythm: **get a quick result first, then make it better**.

| Area | Quick win | Then improve with… | What you'll notice |
|---|---|---|---|
| Dashboard | A dashboard straight on the raw tables | **Metric views**: each KPI is defined once, with business names | The same numbers everywhere, and much less SQL per visual |
| Genie | A Genie space on the raw tables | **Descriptions** in Unity Catalog, then **instructions**, sample questions and metric views | Genie's answers go from guesses to correct, trusted answers |
| App | Tab 1: a data table | Tab 2: visuals | A working app, built by describing it to Genie Code |

The data is a copy of a messy **source system**. The column names are cryptic (`str_id`, `nsv`, `gp`, `wk_strt_dt` …), some values are
codes, and **nothing is described**. That's deliberate. The AI tools only become really good once **you** give the data meaning.

---

## 3. The business questions and the data

### The business questions

1. How did we sell **last week** and **year to date**, compared with last year and with **budget**?
2. Which **regions and retailers** are driving or dragging performance?
3. Where is **poor shelf execution** (on-shelf availability, OSA) **costing sales**?
4. Which **promotions** grow sales **profitably**, and which lose money?

### The tables

Your schema contains these tables. Each one is a copy of `hack_14oct`. Working out what each **column** means is part of the challenge.

| Table | What it holds |
|---|---|
| `fact_sales_weekly` | Weekly sell-out sales (point-of-sale): one row per store, product and week |
| `fact_budget_monthly` | Monthly sales budget by region, retailer group and category |
| `fact_store_visits` | Merchandiser visits to stores, with shelf-execution measures |
| `visit_notes` | Free-text notes written by merchandisers during visits |
| `fact_promotions` | Promotions: which product, which retailer group, which mechanic, when |
| `dim_store` | Stores: retailer group, banner, format, region, province, city |
| `dim_product` | Products: category, subcategory, brand, supplier, pack size, price |
| `dim_supplier` | Suppliers (the agency's FMCG clients) |
| `dim_merchandiser` | Field merchandisers (reps) and their team leads |
| `dim_date` | Calendar and fiscal calendar (the fiscal year runs March–February) |

**Good to know:** money is in **ZAR, excluding VAT**. The history covers **3 years of weeks**, ending with the last complete week.

---

## 4. Rules

1. Work **only in your own schema**. `hack_14oct` is read-only, and you copy from it once (Sprint 0).
2. Start every name with your initials: dashboard `JD – …`, Genie space `JD – …`, app `jd-…`. Metric views go in your schema as `mv_…`.
3. Use the **AI help everywhere**: the Databricks Assistant, AI-generated descriptions, the dashboard AI assistant, and Genie Code for the app.
4. After each improvement, **re-ask the same Genie questions** and compare the answers.
5. Use the **hackathon SQL warehouse** for everything (dashboard, Genie, app).
6. Stuck for more than 5 minutes? Raise a hand, and check [Troubleshooting](#troubleshooting).

---

## 5. The day at a glance

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

## Sprint 0: Your setup (15 min)

**Goal:** your own schema, with a full copy of the hackathon data.

**Steps**
1. Open the hackathon folder in the workspace, then open **`attendees/01_attendee_setup`**.
2. Attach the notebook to **serverless** compute (top right: *Connect* → *Serverless*).
3. Fill in the widgets at the top:
   - `catalog`: the catalog name from your facilitator
   - `warehouse_id`: the SQL warehouse ID from your facilitator
   - `my_schema`: **leave it blank**. Your schema is named after you (for example `jane_doe`).
4. Click **Run all**. It takes 1–2 minutes. The notebook will:
   - create your schema
   - copy every table from `hack_14oct` with `DEEP CLONE` (an independent copy you can change freely)
   - copy the primary and foreign keys (Genie uses them to join tables)
   - check the row counts, and show that **0% of the columns are described** and that you have **no metric views** yet
5. Read the **💡 Hints** section at the end of the notebook. It explains what you'll need to add during the day.

**Check your work**
- Open **Catalog Explorer** (left sidebar) → `<hack_catalog>` → your schema. You should see 10 tables.
- Open `fact_sales_weekly` → **Sample data**. Look at the column names. Can you guess what `nsv`, `gp` or `prm_flg` mean?
- Open the **Lineage** tab. You'll see your table comes from `hack_14oct`.

> **Broke your data later?** Just run `01_attendee_setup` again. It resets your tables. Your dashboards, metric views and Genie space aren't affected.

---

## Sprint 1: Dashboard quick win (30 min)

**Goal:** a first, published dashboard. Speed matters more than polish.

**Steps**
1. **Create the dashboard.** Left sidebar → **Dashboards** → **Create dashboard**. Rename it `<initials> – Monday Command Centre`.
2. **Add data.** Open the **Data** tab → **Add data source**, and pick your tables (`fact_sales_weekly`, `dim_store`, `dim_product`,
   `dim_date`, `fact_budget_monthly`, `fact_store_visits`). You can also write a SQL dataset that joins them.
3. **Set the warehouse.** Make sure the dashboard uses the hackathon SQL warehouse.
4. **Build visuals with the AI assistant.** On the **Canvas**, add a visualization and describe what you want in plain English. For example:
   - *"Total net sales for the last complete week as a counter"*
   - *"Weekly sales trend, this year vs last year"*
   - *"Sales by region as a bar chart"*
   - *"Table of retailers with sales and growth"*
5. **Add filters** for Week range, Region, Retailer and Category, and connect them to the visuals.
6. **Publish** (top right). That's dashboard **v1**.

**Aim for 4–6 visuals on one page:**
- KPI counters: Sales last week, Sales YTD, Budget attainment %, Avg OSA %
- Weekly sales trend (this year vs last year)
- Sales by region (bar, or a map using the store latitude and longitude)
- Retailer table: sales, growth, budget variance

**What to notice:** the assistant has to **guess** which columns mean "sales" or "region", and every visual repeats its own SQL.
Note where it guessed wrong. You'll fix that in Sprint 2.

---

## Sprint 2: Metric views (45 min)

**Goal:** define your KPIs **once**, with business names, and rebuild the dashboard on them.

### What is a metric view?

A metric view is a Unity Catalog object, written in YAML, that has three parts:
- **source and joins:** the fact table, and the dimension tables joined to it
- **dimensions:** the things you group and filter by (Week, Region, Retailer …), with readable names
- **measures:** the KPIs (Sales, Margin % …), defined once as aggregations

You query a metric view with `MEASURE()`: `SELECT Region, MEASURE(Sales) FROM mv_sales GROUP BY ALL`. Ratios like **Margin %**
stay correct at any grouping, because the metric view computes them as `SUM(…) / SUM(…)`, not as an average of percentages.

### Steps

1. **Create `mv_sales`.** Open the **SQL editor**, paste the starter from [Appendix A](#appendix-a-metric-view-starter-fill-in-the-todos),
   replace `<hack_catalog>` and `<your_schema>`, and fill in the TODOs. Or use Catalog Explorer → your schema → **Create** → **Metric view**.
2. **Test it.** Run the `SELECT … MEASURE(Sales) …` query at the end of the starter. Check that the numbers look sensible.
3. **Build all three metric views:**

   | Metric view | Built on | Measures to build |
   |---|---|---|
   | `mv_sales` | `fact_sales_weekly` + stores, products, dates | Sales, Units, Margin, **Margin %**, YoY growth %, Promo Sales |
   | `mv_budget` | `fact_budget_monthly` | Budget, Actual, **Variance %** |
   | `mv_execution` | `fact_store_visits` + stores | Visits, **Avg OSA %**, Avg POG compliance %, % of stores below the 85% OSA target |

4. **Make them discoverable.** Add a `comment` to the metric view, and comments, display names and synonyms to dimensions and measures
   (for example `Sales`: "Net sales value in ZAR excl. VAT, also called revenue or NSV").
5. **Rebuild the dashboard.** In your dashboard's **Data** tab, add the metric views as data sources and switch your visuals to them.
   That's dashboard **v2**. Compare it with v1: are the numbers consistent? Is each visual simpler?
6. **Add a "Why?" page** with a drill-down (region → retailer → store) and an "OSA vs sales growth by region" visual.
7. **Publish** again.

**Tips**
- Look at the data before you write a measure: `SELECT * FROM <your_schema>.fact_sales_weekly LIMIT 20`.
- Ask the Assistant: *"Which column in fact_sales_weekly holds the units sold?"* or *"Write a metric view measure for margin %"*.
- Filtered measures use `FILTER`, for example `SUM(source.nsv) FILTER (WHERE …)`.
- If the YAML fails, check the indentation (spaces, not tabs) and that every column name exists.

### ⭐ Bonus: build a custom visual

Finished early? Add a **custom visual** to your dashboard: a **bullet chart of Sales vs Budget by region**, which the built-in chart types
can't draw. AI/BI dashboards render custom visuals from a **Vega-Lite** spec (*Custom Viz*). See [Appendix D](#appendix-d--bonus-custom-visual-vega-lite).

---

## Sprint 3: Genie quick win (25 min)

**Goal:** a Genie space on the raw tables, and a first look at how well it answers.

**Steps**
1. Left sidebar → **Genie** → **New**. Name it `<initials> – Monday Genie`.
2. Add your **tables** (not the metric views yet): `fact_sales_weekly`, `fact_budget_monthly`, `fact_store_visits`, `fact_promotions`,
   `dim_store`, `dim_product`, `dim_date`.
3. Select the hackathon **SQL warehouse**.
4. Ask these **10 questions exactly as written**, one at a time:
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
5. For each answer, open **Show code** and look at the SQL Genie wrote. Note which answers look wrong or unclear, and why.

**What to look for**
- Did Genie pick the right column for "sales" (net or gross)?
- Did it use the **fiscal** year (March–February) or the calendar year?
- Did it know what "OSA target" means, or what a promotion "mechanic" is?
- Did it join the tables correctly?

Keep your notes. You'll ask the same questions again in Sprint 4.

---

## Sprint 4a: Describe your data (20 min)

**Goal:** give every table and column a clear description in Unity Catalog. **This is one of the most important skills of the day:**
descriptions are written once and then used everywhere, by Genie, the Assistant, the dashboard AI and anyone browsing the catalog.

**Steps**
1. **Table descriptions.** Catalog Explorer → your schema → a table → **Overview** → **AI generate** the description. Read it, fix it,
   then **Save**. Include the **grain** ("one row per store, product and week").
2. **Column descriptions.** Open the **Columns** tab → use the AI suggestions → **review and correct each one** before accepting it.
3. **Start with the columns behind the 10 questions:**
   - `fact_sales_weekly`: `nsv`, `gsv`, `gp`, `qty`, `prm_flg`, `wk_strt_dt`
   - `fact_budget_monthly`: `bgt_nsv`, `mth_strt_dt`
   - `fact_store_visits`: `osa_pct`, `pog_comp`, `vst_dt`
   - `fact_promotions`: `mech`, `prm_typ`, `disc`
   - `dim_store`: `rgn`, `rtl_grp`, `fmt_cd`
   - `dim_date`: `fy_cd`, `fy_q`, `fy_wk`
4. **Explain the codes.** If a column holds codes, look at its values (`SELECT DISTINCT fmt_cd FROM <your_schema>.dim_store`) and
   write what each code means.
5. **Faster in bulk (optional):** ask the Assistant to write the SQL for a whole table, review it, then run it:
   ```sql
   COMMENT ON TABLE <your_schema>.fact_sales_weekly IS '…';
   ALTER TABLE <your_schema>.fact_sales_weekly ALTER COLUMN nsv COMMENT 'Net sales value in ZAR excl. VAT …';
   ```
6. **Tags (optional):** add tags such as `domain = sales` to your tables.
7. **Re-ask the same 10 questions in Genie, without changing anything else**, and compare the answers with your Sprint 3 notes.

**AI drafts are a start, not the answer.** AI-generated descriptions can sound right but be wrong, especially for abbreviations and codes.
Always check them against the data. The [cheat-sheet in Appendix B](#appendix-b-cheat-sheets) shows what a good description includes.

---

## Sprint 4b: Tune Genie (30 min)

**Goal:** turn your Genie space into one a client could trust. Change **one thing at a time**, then re-ask the questions that still look wrong.

| Step | Where in the Genie space | What to add | Example |
|---|---|---|---|
| 1. General instructions | Instructions (text) | Business rules in plain language | "Sales means net sales value (`nsv`). The fiscal year runs March–February. 'Last week' is the last complete week. The OSA target is 85%. 'Furthest below budget' means the lowest variance %. Currency is ZAR." |
| 2. Space-level refinements | Data / table settings | Synonyms for columns, hide columns you don't need | `osa_pct`: "OSA", "availability", "in-stock" |
| 3. Sample questions | Settings | 5–8 starter questions a client would ask on a Monday | "Which regions are below budget this fiscal quarter?" |
| 4. SQL expressions | Instructions → SQL expressions | Reusable measures, filters and dimensions | Measure `Margin % = SUM(gp) / SUM(nsv)`, filter `Open stores` |
| 5. Joins and example SQL | Instructions → joins / SQL queries | Join relationships, and a worked SQL example for a hard question | Year-on-year growth; joining visits to sales by store and week |
| 6. Metric views | Data | Add `mv_sales`, `mv_budget` and `mv_execution` | Genie can then use your governed KPIs directly |
| 7. Trusted assets | Instructions → SQL functions | A Unity Catalog SQL function for a parameterised question | A store summary function that takes a store ID |

**Tips**
- Keep instructions short and specific. One rule per line works best.
- If an answer is wrong, open **Show code**, find what Genie misunderstood, and fix exactly that.
- Use the 👍 / 👎 feedback on answers while you test.

---

## Sprint 5: App (20 min)

**Goal:** a deployed Databricks App with two tabs, built by **describing** it to Genie Code instead of coding it by hand.

**Steps**
1. **Create the app.** Left sidebar → **Compute** → **Apps** → **Create app** → start from a **Streamlit** template.
   Name it `<initials>-command-centre`.
2. **Add the SQL warehouse as a resource** (permission *Can use*), so the app can query your metric views.
3. **Open Genie Code** on the app's source code and paste the **Stage 1** prompt from [Appendix C](#appendix-c-app-with-genie-code).
   Review what it changes.
4. **Deploy** and open the app URL. If the table shows a permission error, grant the app's **service principal** access to your schema
   (the SQL is in Appendix C). You'll find the service principal on the app's details page.
5. Paste the **Stage 2** prompt to add the visuals tab, then **deploy** again.

**Done when:** Tab 1 shows a filterable table, Tab 2 shows the visuals, and changing a filter updates both.

**Tips**
- Do Tab 1 completely (built, deployed, working) before starting Tab 2.
- Make small follow-up requests: *"add a CSV download"*, *"show Margin % below 20% in red"*.
- Don't change the app's start command or port.

---

## Demo (5 volunteers, 3 minutes each)

Tell a **before → after** story:
1. **The Monday question** (15 s): which business question you're answering.
2. **Dashboard v1 → v2** (45 s): what changed when you moved to metric views.
3. **Genie, before and after** (60 s): one question, and how the answer improved after descriptions and tuning.
4. **The insight and the action** (30 s). For example: *"Region Y is below budget. Its OSA dropped below 85%, and its stores lost sales.
   Promotion X drives volume but loses money. This week: send the field team to Region Y, and stop promotion X."*
5. **The app** (30 s).

**Prepare in 5 minutes:** open your dashboard, Genie space and app in separate browser tabs, and pick your one Genie question in advance.

---

## Troubleshooting

| Problem | What to do |
|---|---|
| `01_attendee_setup` says *permission denied* on the catalog or `hack_14oct` | Ask your facilitator for `USE CATALOG` + `CREATE SCHEMA` on the catalog, and `SELECT` on `hack_14oct` |
| The setup notebook warns it can't access the warehouse | Check the warehouse ID, or ask your facilitator for **CAN USE** on the warehouse |
| My tables are messed up | Run `01_attendee_setup` again. It resets your copy |
| Metric view YAML error | Check the indentation (spaces only), the `$$ … $$` around the YAML, and that every column name exists in the table |
| `MEASURE()` error | Use the **measure name** from your YAML, in backticks if it has spaces or symbols: ``MEASURE(`Margin %`)`` |
| Dashboard visual shows no data | Check the filters and the dataset, and that the dashboard uses the hackathon warehouse |
| Genie gives a different number from my dashboard | Point both at the **same metric view** |
| Genie still gets the fiscal year wrong | Check the descriptions of the `dim_date` fiscal columns, and add a clear instruction |
| App shows *permission denied* | Grant the app's service principal `USE SCHEMA` + `SELECT` on your schema (Appendix C) |
| App shows as running but won't load | Don't change the start command or port. Redeploy, and check the app logs |
| I can't find *Custom Viz* | It's in Public Preview. Ask your facilitator |

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
For `mv_budget` and `mv_execution`, follow the same pattern with `fact_budget_monthly` and `fact_store_visits` as the source.

---

## Appendix B: Cheat-sheets

### What a good description includes

| Include | Example |
|---|---|
| Business meaning | "Net sales value after discounts and returns" |
| Unit and currency | "in ZAR, excl. VAT", "percentage 0–100" |
| Grain (table level) | "One row per store, product and week" |
| Codes and allowed values | "`prm_flg`: Y = on promotion, N = regular price", "`fmt_cd`: HYP = hypermarket …" |
| Abbreviations spelled out | "OSA = on-shelf availability" |
| How it joins | "Joins to dim_store.str_id" |
| Synonyms | "also called availability, in-stock rate" |

**Weak:** "Sales column." **Strong:** "Net sales value in ZAR excl. VAT, after promotional discounts. Also called sales or NSV."

### Common terms

| Term | Meaning |
|---|---|
| **NSV / GSV** | Net / gross sales value |
| **OSA** | On-shelf availability: % of the expected products found on shelf during a visit |
| **POG compliance** | Planogram compliance: % of shelf matching the agreed layout |
| **Share of shelf** | The brand's share of shelf space in its category |
| **Sell-out** | Sales from the retailer to shoppers (point-of-sale data) |
| **Fiscal year (FY)** | March to February |
| **Promotion mechanic** | How a promotion works, for example "20% Off" or "Buy 2 Get 1 Free" |
| **Merchandiser / rep** | A field team member who visits stores |

### Useful SQL

```sql
-- Look at a table
SELECT * FROM <your_schema>.fact_sales_weekly LIMIT 20;

-- See the distinct codes in a column
SELECT fmt_cd, count(*) FROM <your_schema>.dim_store GROUP BY ALL;

-- See which columns still have no description
SELECT table_name, column_name FROM <hack_catalog>.information_schema.columns
WHERE table_schema = '<your_schema>' AND (comment IS NULL OR comment = '');
```

---

## Appendix C: App with Genie Code

Create an app named `<initials>-command-centre` (Compute → Apps → Create app, with the SQL warehouse added as a resource).
Open **Genie Code** and build it in two stages.

**Stage 1: Tab 1 "Data" (a table)**
> Build a Streamlit Databricks App called "<initials> Command Centre" with two tabs: "Data" and "Insights". Leave "Insights" empty for now.
> On the "Data" tab, query `<hack_catalog>.<your_schema>.mv_sales` through the SQL warehouse app resource, using `MEASURE()` for
> Sales, Units and Margin %, grouped by Region, Retailer, Category and Week. Show the result as a sortable table, with sidebar filters
> for Region, Retailer, Category and a week range. Format currency as ZAR and Margin % as a percentage. Cache the query results.

✅ Deploy, open the app URL, and check that the filters work. Then grant your app's service principal access to your schema:

```sql
GRANT USE SCHEMA, SELECT ON SCHEMA <hack_catalog>.<your_schema> TO `<app-service-principal-application-id>`;
```

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
