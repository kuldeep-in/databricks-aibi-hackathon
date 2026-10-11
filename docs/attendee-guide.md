# Perfect Store Command Centre: Attendee Guide

**Databricks Hackathon · 4 hours · AI/BI Dashboards · Metric Views · Genie · Databricks Apps (optional)**

> *You are the insights team at a fictional retail-execution agency. Your FMCG clients ask every Monday: how did we sell last week,
> did we hit budget, and what is happening on the shelf? Build the command centre that answers these questions, from a dashboard to a
> trusted Genie to a field-team app.*

This guide tells you **what** to do in each sprint. Your **scenario document** (in `scenarios/`) tells you **which business questions** your
team answers. Facilitators will demo the **how** at the start of each sprint, so watch the demo, then build.

---

## 1. Before you start

| Item | Value |
|---|---|
| Workspace URL | `<workspace-url>` |
| Catalog | `<hack_catalog>` |
| Source data (read-only) | `<hack_catalog>.hack` |
| Your team schema | `<hack_catalog>.team_XX` (your team number, for example `team_03`) |
| SQL warehouse | `<warehouse-A>` (teams 1–3) / `<warehouse-B>` (teams 4–5) |
| Team setup notebook | `<workspace-path>/01_team_setup` |
| Scoreboard | `<scoreboard-link>` |

**Checklist:** ☐ I can log in ☐ I know my team number ☐ I've opened my team's scenario document

---

## 2. Your team and scenario

| Team | Scenario | Persona | Document |
|---|---|---|---|
| Team 01 | A | Supplier Account Manager | [scenarios/A-supplier-account-manager.md](scenarios/A-supplier-account-manager.md) |
| Team 02 | B | Field Operations Manager | [scenarios/B-field-operations-manager.md](scenarios/B-field-operations-manager.md) |
| Team 03 | C | Trade Marketing Manager | [scenarios/C-trade-marketing-manager.md](scenarios/C-trade-marketing-manager.md) |
| Team 04 | D | Client Executive | [scenarios/D-client-executive.md](scenarios/D-client-executive.md) |
| Team 05 | E | Insights Analyst | [scenarios/E-insights-analyst.md](scenarios/E-insights-analyst.md) |

**Suggested roles (4 people):** BI builder (dashboard), business expert (descriptions, Genie instructions, storytelling),
data modeller (metric views), and app builder (optional App track, otherwise a second BI builder).

---

## 3. Rules

1. Work **only in your team schema** (`team_XX`). `hack` is read-only, and you copy from it once.
2. Name everything with your team prefix: dashboard `T03 – …`, Genie space `T03 – …`, app `t03-…`, metric views `mv_…`.
3. Use the **AI help everywhere**: the Assistant, AI-generated descriptions, AI-assisted dashboard widgets, and Genie Code for the app.
4. **Record every Genie score** on the scoreboard (baseline, after descriptions, final).
5. Stuck for more than 5 minutes? Raise a hand. Facilitators have a starter asset for every sprint.

---

## 4. The day at a glance

| Time | Sprint | What you do | Done when |
|---|---|---|---|
| 0:00 – 0:15 | Kick-off | Hear the storyline, sit with your team, open your scenario | Team formed |
| 0:15 – 0:30 | **0. Team setup** | Create your schema and copy the data | ✅ Tables in `team_XX` |
| 0:30 – 1:00 | **1. Dashboard quick win** | Build a first dashboard straight on your tables | ✅ Dashboard v1 published |
| 1:00 – 1:45 | **2. Metric views** | Define your KPIs once as metric views, and rebuild the dashboard on them | ✅ Dashboard v2 on metric views |
| 1:45 – 1:55 | Break | | |
| 1:55 – 2:20 | **3. Genie quick win** | Create a Genie space and ask your 10 test questions | ✅ Baseline score recorded |
| 2:20 – 2:40 | **4a. Describe your data** | Add table and column descriptions in Unity Catalog, then re-ask the 10 questions | ✅ "After descriptions" score recorded |
| 2:40 – 3:10 | **4b. Tune Genie** | Instructions, sample questions, SQL expressions, metric views, benchmarks | ✅ Final score recorded |
| 3:10 – 3:30 | **5. Choose a track** | Polish, AI Functions, **or** the optional App | ✅ Demo ready |
| 3:30 – 3:55 | Demos | 3 min demo + 1 min Q&A per team | |
| 3:55 – 4:00 | Awards | | |

---

## 5. What to do in each sprint (high level)

### Sprint 0: Team setup (15 min)

1. **One person** opens `01_team_setup`, sets `team_schema = team_XX`, and clicks **Run all**.
2. Everyone opens **Catalog Explorer → `<hack_catalog>` → `team_XX`** and checks that the tables are there.
3. Look at a few tables. Notice the **lineage** back to `hack`, and that the tables have **almost no descriptions**. You'll fix that later.

### Sprint 1: Dashboard quick win (30 min)

1. Create an **AI/BI Dashboard** named `T0X – <scenario name>`.
2. Add your team tables as datasets (for example the weekly sales fact table and its dimensions).
3. Use the **AI assistant** in the dashboard to create 4–6 visuals for your scenario's questions, and add 2–3 filters (for example Week, Region, Retailer).
4. **Publish** it. That's dashboard **v1**.

> Don't aim for perfection. Get something working quickly. Notice how much SQL or guessing each visual needs.

### Sprint 2: Metric views (45 min)

1. Create your first **metric view** in `team_XX` (template in Appendix A), with dimensions such as Week, Region, Retailer, Category and Brand,
   and measures such as Sales, Units, Margin and **Margin %**.
2. Query it with `MEASURE()` in the SQL editor and check that the numbers look right.
3. Add the business measures your scenario needs (see your scenario document), for example YoY growth %, Budget variance or OSA %.
4. Add descriptions, display names and synonyms to your measures.
5. **Switch your dashboard datasets** to the metric views. That's dashboard **v2**. Compare it with v1.

### Sprint 3: Genie quick win (25 min)

1. Create a **Genie space** named `T0X – <scenario name> Genie`, using your team **tables** (not the metric views yet).
2. Ask the **10 test questions** from your scenario document **exactly as written**.
3. Mark each answer correct or incorrect, and record the **baseline score** on the scoreboard.

### Sprint 4a: Describe your data (20 min, a key capability)

1. In **Catalog Explorer**, open each team table and use **AI generate** for the table description, then for the column descriptions.
2. **Review every suggestion.** The business expert corrects the meanings, units (ZAR, %), grain and abbreviations (Appendix B).
3. Concentrate on the tables and columns behind your 10 test questions first.
4. *(Optional)* Bulk-edit with SQL `COMMENT ON` / `ALTER COLUMN … COMMENT`, and add tags.
5. **Re-ask the same 10 questions without changing anything else**, and record the **"after descriptions" score**.

### Sprint 4b: Tune Genie (30 min)

Work through this list from the top. After each step, re-ask the questions that are still wrong:

1. **General instructions:** business rules (what "sales" means, the fiscal year March–February, what "top" means, currency ZAR).
2. **Space-level refinements:** synonyms, hide columns you don't need.
3. **Sample questions:** 5–8 starter questions for your persona.
4. **SQL expressions:** reusable measures and filters.
5. **Joins and example SQL** for the hard questions.
6. **Add your metric views** to the space.
7. *(Stretch)* **Trusted assets:** a UC SQL function for a parameterised question.
8. **Benchmarks:** load your 10 questions and run the evaluation.

Record your **final score** on the scoreboard.

### Sprint 5: Choose a track (20 min)

| Track | What to do |
|---|---|
| **a. Polish** | Improve the dashboard layout, add drill-downs, schedule a subscription, embed Genie in the dashboard |
| **b. AI Functions** | Use `ai_classify` / `ai_query` on the visit notes, save the result to `team_XX`, and add it to the dashboard |
| **c. App (optional)** | Build a two-tab Databricks App with **Genie Code** (Appendix C): **Tab 1** shows a data table, **Tab 2** shows visuals |

### Demo (3 minutes per team)

Tell a **before → after** story:
1. The persona and their question (15 s).
2. Dashboard v1 → v2 on metric views: what changed (45 s).
3. Genie: a live question, plus your score from **baseline → after descriptions → final** (60 s).
4. The insight you found and the action the persona should take (30 s).
5. *(Optional)* The app (30 s).

---

## 6. How you'll be judged

| Criterion | Points |
|---|---|
| Business value and storytelling | 20 |
| Dashboard quality (v2) | 15 |
| Metric views | 15 |
| Data descriptions (coverage and quality) | 15 |
| Genie: final accuracy | 15 |
| Genie: improvement from baseline to final | 10 |
| Creativity and use of AI features | 10 |
| **Bonus:** App Stage 1 (+5), Stage 2 (+5) | +10 |

---

## Appendix A: Metric view starter template

> Column names are examples. Check the real names in **Catalog Explorer** and adjust.

```sql
CREATE OR REPLACE VIEW <hack_catalog>.team_XX.mv_sales
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.1
comment: "Weekly sell-out KPIs"
source: <hack_catalog>.team_XX.fact_sales_weekly
joins:
  - name: store
    source: <hack_catalog>.team_XX.dim_store
    on: source.store_id = store.store_id
  - name: product
    source: <hack_catalog>.team_XX.dim_product
    on: source.sku_id = product.sku_id
dimensions:
  - name: Week
    expr: source.week_start_date
  - name: Region
    expr: store.region
  - name: Retailer
    expr: store.rtl_grp
  - name: Category
    expr: product.category
  - name: Brand
    expr: product.brand
measures:
  - name: Sales
    expr: SUM(source.nsv)
  - name: Units
    expr: SUM(source.units)
  - name: Margin
    expr: SUM(source.margin)
  - name: Margin %
    expr: SUM(source.margin) / NULLIF(SUM(source.nsv), 0)
$$;

SELECT Region, MEASURE(Sales) AS sales, MEASURE(`Margin %`) AS margin_pct
FROM <hack_catalog>.team_XX.mv_sales
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
| Codes and allowed values | "`promo_flag`: Y = on promotion, N = regular price" |
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

### Genie scoring

- **Correct:** the right number(s) and the right filters/time period. The SQL looks sensible.
- **Incorrect:** a wrong number, a wrong period or filter, or Genie asks for clarification.
- Ask questions **exactly as written** every time, so the scores are comparable.

---

## Appendix C: Optional App track with Genie Code

Your app is pre-created (`t0X-command-centre`) with the SQL warehouse attached. Open it, open **Genie Code**, and build it in two stages.

**Stage 1: Tab 1 "Data" (a table)**
> Build a Streamlit Databricks App called "T0X Command Centre" with two tabs: "Data" and "Insights". Leave "Insights" empty for now.
> On the "Data" tab, query `<hack_catalog>.team_XX.mv_sales` through the SQL warehouse app resource, using `MEASURE()` for
> Sales, Units and Margin %, grouped by Region, Retailer, Category and Week. Show the result as a sortable table, with sidebar filters
> for Region, Retailer, Category and a week range. Format currency as ZAR and Margin % as a percentage. Cache the query results.

✅ Deploy, open the app URL, and check that the filters work. Then grant your app's service principal access to your schema:
`GRANT USE SCHEMA, SELECT ON SCHEMA <hack_catalog>.team_XX TO \`<app-sp-application-id>\`;`

**Stage 2: Tab 2 "Insights" (visuals)**
> On the "Insights" tab, add KPI tiles for Sales, Margin % and YoY growth from `mv_sales`, and OSA % from `mv_execution`. Below them, add
> a weekly sales trend line chart and a bar chart of sales by Region. Use the same sidebar filters as the "Data" tab.

✅ Changing a filter updates both tabs. To refine, use small follow-up prompts ("add a CSV download", "highlight Margin % below 20% in red").
Don't change the app's start command or port.
