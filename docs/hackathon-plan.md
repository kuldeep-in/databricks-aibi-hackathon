# Databricks Hackathon: Perfect Store Command Centre

**AI/BI Dashboards · Metric Views · Genie · Databricks Apps (optional)**

**Format:** 4 hours, in person, hands-on · **Participants:** 20 (5 teams of 4) · **Workspace:** customer-provided, Unity Catalog enabled, no data yet

> Names in `<angle brackets>` are placeholders to confirm with the customer
> (catalog name, group names, warehouse name).

---

## 1. Goals and approach

### Approach: "quick win first, then make it better"

Every module follows the same rhythm, so attendees get results within minutes and then learn *why* the governed way is better:

```
 QUICK WIN (≈25 min)                      IMPROVE (≈35 min)                         PROVE IT
 ─────────────────────                    ─────────────────────                     ──────────────
 Dashboard straight on the team tables →  Rebuild on METRIC VIEWS (one definition →  Same numbers everywhere,
 using AI-assisted widgets                of Sales, Margin %, YoY, OSA %)            and less SQL per widget

 Genie space on the undocumented tables, →  1) DESCRIBE THE DATA in UC (table and    →  Genie accuracy score at
 asking 10 test questions (baseline)        column descriptions, AI-generated then      every step: baseline →
                                            reviewed)                                   after descriptions →
                                            2) instructions, sample questions, SQL      final
                                            expressions, metric views, benchmarks
```

### Outcomes: by the end, each team has

| # | Deliverable | Status |
|---|---|---|
| 1 | An **AI/BI Dashboard**: a quick version first, then rebuilt on metric views | **Core** |
| 2 | One or more **UC Metric Views** that define the team's business KPIs once | **Core** |
| 3 | **Documented data:** table and column descriptions on every table in the team schema, AI-generated and then reviewed by the team | **Core (key capability)** |
| 4 | A **Genie space** with a baseline accuracy score, a score after adding descriptions, and a final score after tuning (instructions, sample questions, metric views, and so on) | **Core** |
| 5 | A **Databricks App** built with Genie Code: Tab 1 shows a data table, Tab 2 shows visuals | **Optional** (stretch track, see section 7) |
| 6 | A 3-minute demo showing the "before → after" improvement | **Core** |

### Theme (locked): "Perfect Store Command Centre: from sell-out to shelf"

> *"You are the insights team at a fictional retail-execution agency. Your FMCG clients ask every Monday: how did we sell last week,
> did we hit budget, and what is happening on the shelf? Build the command centre that answers these questions, from a dashboard to a
> trusted Genie to a field-team app."*

**Why this theme:** it reflects everyday retail-execution work, joining sell-out sales (weekly supplier business overviews),
budget vs actual, and in-store execution (merchandiser visits, OSA, planogram compliance). Attendees
already know the shape of the data, and the key insight (execution gaps costing sales) can only be found by combining sales and execution data.

**Ground rules for the data:** fictional retailers, suppliers and brands only (no real client or retailer names), currency **ZAR**,
a **South African** region/province store hierarchy, and a **March–February fiscal year**.

All five challenge cards (section 8) are personas inside this one theme, so every team works with the same story and the same data.

---

## 2. Data strategy: one catalog, one source schema, a schema per team

### Decision

**One catalog for the whole hackathon, with one read-only source schema. Each team creates its own schema and copies the data into it.**

```
<hack_catalog>                          one catalog for the whole event
├── hack_14oct         (READ-ONLY)     ← facilitator loads the sample data here (single source of truth), with minimal descriptions on purpose
│     ├── dim_* / fact_* tables
│     └── visit_notes
├── facilitator_kit    (FACILITATOR ONLY) ← answer keys: fully described reference tables, metric views, Genie config, starter dashboards
├── team_01            (OWNED BY TEAM)  ← created by the team on the day; data copied from hack_14oct
├── team_02
├── ...
└── team_05
```

**How it works**

1. The facilitator builds `hack_14oct` before the day and makes it **read-only** for all participants.
2. At the start, each team **creates its own schema** (`team_XX`) and **copies the source tables into it** with a ready-made script (section 3.2).
3. From then on, teams work **only in their own schema**. Their dashboards, metric views, Genie space and (optional) app all point at `team_XX.*`.
4. Teams **own the metadata** of their copy. They write the table and column descriptions themselves (section 5), and can change
   the copy freely (add columns, views, metric views, write-back) without affecting anyone else.
5. `facilitator_kit` holds the "answer key" versions (reference metric views, a tuned Genie config, starter dashboards).
   It isn't granted to participants, so teams build their own. The facilitator only shares pieces if a team gets stuck.

**Why this model works**

| Benefit | Detail |
|---|---|
| Simple to administer | One catalog, one data load, one small grant script |
| Teams own their data **and its descriptions** | They can `COMMENT ON` tables and columns, accept AI-generated descriptions, `ALTER`, create metric views and write back without asking for grants. **This is why we copy instead of sharing one schema** |
| Safe | `hack_14oct` is read-only. A team that breaks its own data just re-runs the copy script |
| Teams grant their own app's access (optional App track) | The team owns its schema, so it can grant its app's service principal access itself |
| Shows Unity Catalog in action | Ownership, grants, lineage (`hack_14oct` → `team_XX` → metric view → dashboard/Genie), cloning |
| Easy cleanup | `DROP SCHEMA <hack_catalog>.team_XX CASCADE`, or drop the whole catalog |

**Trade-offs to manage**

- **Storage:** 5 copies. At about 5M rows that's small (a few hundred MB at most).
- **Drift:** team numbers can differ after their changes. That's acceptable, because Genie test answers are checked against each team's own data.
- **Constraints:** the copy script re-applies the PK/FK constraints, because Genie uses them for joins. Descriptions are deliberately left for the teams to write.

### Team structure

- **5 teams of 4.** Each team has a mix of roles: 1 analyst/BI person, 1 business SME, 1–2 technical people (the App track is optional).
- **Schema naming is fixed:** `team_01` … `team_05`.
- **Ownership:** one member creates the schema, then transfers ownership to the team group (`ALTER SCHEMA ... OWNER TO team_XX`).
- **Asset naming:** dashboard `T03 – Trade Performance`, metric view `team_03.mv_sales`, Genie space `T03 – Trade Genie`, app `t03-command-centre`.

### Fallback (if the customer can't create a new catalog)

Use one existing catalog that the customer assigns, and create `hack_14oct`, `facilitator_kit` and the team schemas inside it. Nothing else changes.

---

## 3. Sample data design

> **Status:** the data is **synthetic and generated** by the `03_generate_synthetic_data` notebook, which Step 3 of
> `00_facilitator_runbook` calls. It writes the tables below **directly as Delta tables** in `hack_14oct`. Each team then copies them
> into its own schema with `01_team_setup`.
> The attendee guide, metric view template, Genie test questions and app prompts refer to these table and column names.

The data needs to be *realistic and full of insight* (seasonality, under-performing regions, promo uplift, out-of-stock patterns) so that Genie
and the dashboards have something to find.

### 3.1 Tables (`<hack_catalog>.hack_14oct`): target data contract

| Table | Grain | Approx. rows | Purpose |
|---|---|---|---|
| `dim_date` | day (week/month/quarter/fiscal attributes) | ~1,100 (3 yrs) | Time intelligence |
| `dim_store` | store | 120 | Retailer group, banner, region, province, city, format, lat/long |
| `dim_product` | SKU | 200 | Category → subcategory → brand → SKU, pack size, supplier |
| `dim_supplier` | supplier | 22 | Supplier name, tier, category type (Food / GM / Liquor) |
| `dim_merchandiser` | field rep | ~20 | Rep name, team lead, region |
| `fact_sales_weekly` | week × store × SKU (156 weeks) | ~350K | Units, sales value, cost, margin, promo flag |
| `fact_budget_monthly` | month × region × retailer × category | ~10K | Budget vs actual |
| `fact_promotions` | promo × SKU × retailer group | ~1,000 | Promo type, mechanic, start/end, discount % |
| `fact_store_visits` | visit | ~30K | Rep, store, duration, on-shelf availability (OSA) %, planogram compliance %, share-of-shelf % |
| `visit_notes` | visit (free text) | ~9K | Merchandiser comments, for `ai_query` / `ai_classify` challenges |

**Insights to plant deliberately in the data** (they make the demos land):
- A region where sales drop because OSA falls below 85%.
- A promo mechanic (for example "Buy 2 get 1") with high uplift but negative margin.
- Seasonal peaks (December, Easter) and a supplier gaining share.
- Stores where the merchandiser visit frequency predicts compliance.
- **"Trap" questions for Genie:** ambiguous terms such as "sales" (gross or net?), "last quarter" (calendar or fiscal?), and "top stores"
  (by sales or by growth?). The raw-table Genie gets these wrong, and the tuned Genie gets them right. That's the before/after story.

**Data checklist (facilitator, before T-3 days):** run Step 3 (generate), check that the data contract is all ✅, add the PK/FK constraints (Step 5), and build the fully described copy in `facilitator_kit` (Step 6).
keep the business abbreviations, the insights are planted, there are no real client names, and the fully described copy is in `facilitator_kit`.

### 3.1a Description strategy: undocumented on purpose

Writing descriptions is a **key capability to showcase**, so the `hack_14oct` tables ship **almost undocumented**:

| Where | What it contains | Why |
|---|---|---|
| `hack_14oct.*` (what teams copy) | **No descriptions and no metric views.** Cryptic, inconsistent column names (`str_id`, `sku`, `qty`, `nsv`, `gp`, `prm_flg`, `wk_strt_dt`, `rgn`, `fmt_cd`, `osa_pct`, `nt_txt`) and coded values (`fmt_cd` HYP/SUP/CNV/WHS, `sts` O/C, `prm_typ` PR/MB/BN) | Like real source systems. Dashboards and Genie must guess until teams describe the data and build metric views, which gives a clear baseline |
| `facilitator_kit.*` (answer key) | The same tables with full table and column descriptions, synonyms and tags | Used to mark team descriptions, and as a fallback if a team runs out of time |

This makes the impact of descriptions **measurable**: teams record their Genie score before and after describing the data (section 5).

### 3.2 Team copy script (each team runs it in the first 10 minutes)

The facilitator provides one parameterised notebook, `01_team_setup`. A team member sets `team_schema = team_XX` and clicks **Run all** (about 2–3 minutes).

```sql
-- Parameter: :team_schema  (for example 'team_03')
USE CATALOG <hack_catalog>;

-- 1. Create the team schema and hand ownership to the team group
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:team_schema)
  COMMENT 'Hackathon working schema – copied from hack_14oct';
ALTER SCHEMA IDENTIFIER(:team_schema) OWNER TO `team_03`;   -- the team's group

-- 2. Copy every source table. DEEP CLONE makes an independent copy (the minimal source comments come along).
--    (The notebook loops over information_schema.tables, so the list never goes stale.)
CREATE OR REPLACE TABLE IDENTIFIER(:team_schema || '.fact_sales_weekly') DEEP CLONE hack_14oct.fact_sales_weekly;
-- ... the same for every dim_* / fact_* / visit_notes table

-- 3. Re-apply the PK/FK constraints (generated from the source definitions)
-- 4. Validation: row counts match hack_14oct, and constraints are present
```

> Metric views and descriptions are **not** pre-built in team schemas. Building them is the hackathon exercise (Sprints 2 and 4).

| Copy method | Pros | Cons | Use it |
|---|---|---|---|
| `DEEP CLONE` | Independent copy, keeps comments and properties, safe to change | Copies the storage (small here) | **Default** |
| `SHALLOW CLONE` | Instant, and no data is copied | Depends on the source files, so team tables can break if the source is rebuilt | Only if the data is very large |
| `CREATE TABLE AS SELECT` | Simplest to understand | Loses comments and constraints | Teaching moment only |

---

## 4. Metric views: the "improve" step for dashboards and Genie

**What they are:** a UC object that defines business **measures** (Sales, Margin %, YoY growth) and **dimensions** (Region, Category,
Week) **once**, in YAML, on top of tables and joins. Dashboards, Genie and SQL all reuse the same definitions, so "Margin %" means the
same thing everywhere.

### Why it's the improve step

| Quick-win version (raw tables) | Improved version (metric view) |
|---|---|
| Each widget repeats its own SQL (`SUM(sales)/SUM(...)`) | Each widget picks a measure: `MEASURE(\`Margin %\`)` |
| Ratios are often wrong when re-aggregated (an average of averages) | Ratio measures re-aggregate correctly at any grain |
| Genie guesses the joins and what "sales" means | Genie gets the joins, definitions and synonyms from the metric view |
| Different teams get different numbers | One governed definition, with lineage in Catalog Explorer |

### Exercise ladder (Sprint 2)

| Level | Task | Outcome |
|---|---|---|
| **L1: First metric view** | `mv_sales` on `fact_sales_weekly` joined to `dim_store`, `dim_product` and `dim_date`. Measures: Sales, Units, Margin, **Margin %** | Query it with `SELECT Region, MEASURE(Sales) ... GROUP BY ALL` |
| **L2: Business measures** | Add **YoY growth %**, **Avg selling price**, **Promo sales share %**, plus filtered measures (for example `Sales on promo`) | Measures that would take complicated SQL in every widget |
| **L3: More subject areas** | `mv_execution` on `fact_store_visits` (OSA %, compliance %, visits per store), and `mv_budget` (Budget, Actual, Variance %) | One metric view per business domain |
| **L4: Make it discoverable** | Add comments, display names and synonyms to the measures and dimensions | Genie and dashboard users understand the fields |
| **L5: Reuse it** | Switch the dashboard datasets to the metric views, and add the metric views to the Genie space | The before/after comparison for the demo |

### Answer key (attendees get a partly filled starter with TODOs in the attendee guide, Appendix A)

```sql
CREATE OR REPLACE VIEW <hack_catalog>.team_03.mv_sales
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.1                      # use the version in the current docs
comment: "Weekly trade performance – governed sales KPIs"
source: <hack_catalog>.team_03.fact_sales_weekly
joins:
  - name: store
    source: <hack_catalog>.team_03.dim_store
    on: source.str_id = store.str_id
  - name: product
    source: <hack_catalog>.team_03.dim_product
    on: source.sku = product.sku
dimensions:
  - name: Week
    expr: source.wk_strt_dt
  - name: Region
    expr: store.rgn
  - name: Retailer
    expr: store.rtl_grp
  - name: Category
    expr: product.cat
  - name: Brand
    expr: product.brnd
measures:
  - name: Sales
    expr: SUM(source.nsv)
  - name: Units
    expr: SUM(source.qty)
  - name: Margin
    expr: SUM(source.gp)
  - name: Margin %
    expr: SUM(source.gp) / NULLIF(SUM(source.nsv), 0)
  - name: Promo Sales
    expr: SUM(source.nsv) FILTER (WHERE source.prm_flg = 'Y')
$$;

-- Use it
SELECT Region, MEASURE(Sales) AS sales, MEASURE(`Margin %`) AS margin_pct
FROM <hack_catalog>.team_03.mv_sales
GROUP BY ALL
ORDER BY sales DESC;
```

> Teams can also build metric views in the **Catalog Explorer UI** (with the Assistant's help) instead of writing YAML. Both routes are valid.
> Column names match `03_generate_synthetic_data` (cryptic on purpose; see its `RENAMES` map).

---

## 5. Genie: quick win, describe the data, then tune

### Quick win (Sprint 3)

1. Create a Genie space on the team's tables as they are: **undocumented** (`fact_sales_weekly`, the dims, and `fact_store_visits`).
2. Ask the team's **10 test questions** (handed out per challenge card, with expected answers).
3. Record the **baseline score** (for example 4/10) on the team scoreboard.

### Sprint 4a: describe your data in Unity Catalog (key capability)

The team owns its schema, so it can document every table and column itself. **The descriptions are written once in Unity Catalog and
then used everywhere:** by Genie, the Databricks Assistant, AI-assisted dashboard authoring, metric views, and search in Catalog Explorer.

| Step | How | Tip |
|---|---|---|
| **1. AI-generated table descriptions** | Catalog Explorer → table → **Overview** → *AI generate* the description → review → **Accept** or edit | AI gives a first draft. The business SME on the team makes it correct |
| **2. AI-generated column descriptions** | Catalog Explorer → **Columns** tab → AI-suggested descriptions → accept or edit each one | Concentrate on the columns behind the test questions and the abbreviations (`nsv`, `osa_pct`, `fy_wk`) |
| **3. Fix them in SQL (optional, faster in bulk)** | `COMMENT ON TABLE team_03.fact_sales_weekly IS '...';` and `ALTER TABLE team_03.fact_sales_weekly ALTER COLUMN nsv COMMENT 'Net sales value in ZAR, excl. VAT';` | Ask the Assistant to draft the statements for a whole table |
| **4. Tags (stretch)** | Add governed tags such as `domain=sales`, `kpi=true`, `pii=false` | Shows governance and makes data easier to find |
| **5. Re-score Genie** | Ask the same 10 questions again, **without changing anything else** | Record the **"after descriptions" score**. This isolates the value of good metadata |

**What a good description includes** (on the attendee guide cheat-sheet): the business meaning, the **unit and currency**, the **grain**
("one row per store, SKU and week"), allowed values or codes, **abbreviations spelled out**, and common synonyms ("OSA, availability, in-stock").

> Facilitator scoring tip: compare 3–4 team descriptions with the `facilitator_kit` answer key during the sprint, and call out a great one to the room.

### Sprint 4b: Genie tuning ladder. Each step should move the score further

| Level | What to add | Example | Typical fix |
|---|---|---|---|
| **G1: General instructions** | Business rules in plain language | "Sales means net sales value excl. VAT. The fiscal year starts in March. 'Top' means by sales unless stated. Show currency in ZAR" | Ambiguous terms, fiscal periods |
| **G2: Space-level refinements** | On top of the UC descriptions from 4a: add column synonyms in the space, hide irrelevant columns, and add example values | `osa_pct` synonyms: "OSA", "availability", "in-stock" | Wrong column chosen |
| **G3: Sample questions** | 5–8 starter questions shown to users | "Which regions are below budget this fiscal quarter?" | Users get started quickly |
| **G4: SQL expressions** | Reusable measures, filters and dimensions in the space's knowledge store | Filter `Active stores = store_status = 'Open'`, measure `Margin %` | Repeated logic gets defined once |
| **G5: Joins and example SQL** | Define join relationships, and add example SQL queries for the hard questions | YoY growth, share of category | Wrong joins, complex calculations |
| **G6: Metric views as data** | Add `mv_sales`, `mv_execution` and `mv_budget` to the space (alongside the tables or instead of them) | Genie uses `MEASURE(\`Margin %\`)` | The governed KPIs come along for free |
| **G7: Trusted assets** | UC SQL functions for parameterised business questions | `fn_store_scorecard(store_id)` | Answers marked as trusted |
| **G8: Benchmarks** | Load the 10 test questions with expected SQL as benchmarks, and run the evaluation | Accuracy goes from 5/10 to 9/10 | A **proven** improvement, which becomes the demo slide |

**Scoreboard:** a shared sheet (or the facilitator's screen) shows each team's Genie score in three columns: **baseline → after descriptions → final**. It's a friendly competition
and makes the value of tuning very visible.

---

## 6. Agenda (4 hours, core track)

| Time | Sprint | Content | Checkpoint |
|---|---|---|---|
| 0:00 – 0:15 | **Kick-off** | Goals, the "quick win then improve" approach, the **Perfect Store Command Centre** storyline, teams, rules and judging | Teams formed |
| 0:15 – 0:30 | **Sprint 0: Team setup** | Run `01_team_setup` (create `team_XX`, copy the data from `hack_14oct`), then a quick Catalog Explorer tour (lineage, ownership, and notice that the tables have **no descriptions** yet) | Team schema ready |
| 0:30 – 1:00 | **Sprint 1: Dashboard quick win** | 5 min demo, then 25 min build: a dashboard straight on the team tables, using the AI assistant to create widgets, plus filters, then publish | **First dashboard published** |
| 1:00 – 1:45 | **Sprint 2: Metric views** | 10 min demo, then 35 min build: metric view ladder L1–L5, and switch the dashboard to the metric views | **Dashboard v2 on metric views** |
| 1:45 – 1:55 | Break | | |
| 1:55 – 2:20 | **Sprint 3: Genie quick win** | 5 min demo, then 20 min build: a Genie space on the undocumented tables, with the 10 test questions | **Baseline score recorded** |
| 2:20 – 2:40 | **Sprint 4a: Describe your data** | 5 min demo, then 15 min build: AI-generated table and column descriptions, reviewed and edited by the team, then Genie re-scored | **"After descriptions" score recorded** |
| 2:40 – 3:10 | **Sprint 4b: Genie tuning** | 5 min demo, then 25 min build: tuning ladder G1–G8, including adding the metric views | **Final score recorded** |
| 3:10 – 3:30 | **Sprint 5: Choose a track** | **(a) Polish:** dashboard layout, schedules, Genie embedded in the dashboard; **(b) AI Functions:** classify `visit_notes` with `ai_classify`/`ai_query` and add the result to the dashboard; **(c) Optional App track** (section 7) | Demo ready |
| 3:30 – 3:55 | **Demos** | 5 teams × 4 min: show **before → after** (dashboard v1 → v2, Genie score baseline → final) | |
| 3:55 – 4:00 | **Awards and wrap-up** | Winner, next steps, survey | |

> **Nobody gets stuck:** if a team misses a checkpoint, the facilitator gives it the starter asset from `facilitator_kit` (a starter dashboard,
> a reference metric view, a baseline Genie config) and it carries on with the next sprint.

---

## 7. Optional: Databricks Apps track (2 stages, built with Genie Code)

Include the App track only if the customer wants it **and** the workspace supports it (confirm at T-2 weeks).
Teams **don't write the app by hand**. They describe what they want to **Genie Code** (the AI coding agent in the workspace), then
review and deploy what it builds. The app has two tabs, built one stage at a time:

```
 ┌──────────────────────────────────────────────────────────────┐
 │  T03 Command Centre                                          │
 │  [ Tab 1: Data ]  [ Tab 2: Insights ]                        │
 ├──────────────────────────────────────────────────────────────┤
 │  Stage 1 → Tab 1: filterable TABLE of the team's data        │
 │  Stage 2 → Tab 2: VISUALS (KPI tiles + charts), same filters │
 └──────────────────────────────────────────────────────────────┘
```

### Stage 1: Tab 1 "Data", a table (≈10 min)

| | |
|---|---|
| **Goal** | A deployed app with one tab that shows a filterable table from the team's **metric view** (or tables) |
| **Data** | `team_XX.mv_sales`, queried with `MEASURE()`, through the SQL warehouse attached as an app resource |
| **Done when** | The app URL opens, the table loads, and the filters (Region, Retailer, Category, Week range) work |

**Starter prompt for Genie Code:**
> Build a Streamlit Databricks App called "T03 Command Centre" with two tabs: "Data" and "Insights". Leave "Insights" empty for now.
> On the "Data" tab, query `<hack_catalog>.team_03.mv_sales` through the SQL warehouse app resource, using `MEASURE()` for
> Sales, Units and Margin %, grouped by Region, Retailer, Category and Week. Show the result as a sortable table, with sidebar filters
> for Region, Retailer, Category and a week range. Format currency as ZAR and Margin % as a percentage. Cache the query results.

### Stage 2: Tab 2 "Insights", visuals (≈10–15 min)

| | |
|---|---|
| **Goal** | The second tab shows the same data as visuals, driven by the same filters |
| **Content** | 3–4 KPI tiles (Sales, Margin %, YoY growth, OSA %), a sales trend line by week, a bar chart of sales by region or retailer, and, if there's time, a margin-vs-sales scatter by brand |
| **Done when** | Changing a filter updates both tabs |

**Starter prompt for Genie Code:**
> On the "Insights" tab, add KPI tiles for Sales, Margin % and YoY growth from `mv_sales`, and OSA % from `mv_execution`. Below them, add
> a weekly sales trend line chart and a bar chart of sales by Region. Use the same sidebar filters as the "Data" tab, and keep a
> consistent colour palette.

### Tips for teams

- **Iterate in small prompts:** "make the table paginated", "add a download-as-CSV button", "show a Margin % below 20% in red".
- **Use the metric views.** The app then shows exactly the same numbers as the dashboard and Genie, which is a good demo point.
- **Keep the app's start command and port as Genie Code or the template set them.** The app must listen on the port the platform gives it,
  or it shows as running but won't load.
- **Stretch (bonus only):** a third tab with Genie chat through the Genie Conversation API, or embed the published dashboard.

### Timing options

| Option | How | Trade-off |
|---|---|---|
| **Stretch track (default)** | In Sprint 5 (20 min), the technical members of a team build Stages 1 and 2 while the others polish | No change to the core agenda. Stage 2 may be partial |
| **Full App module** | Shorten Sprint 1 and Sprint 3 to 20 min each, and make Sprint 5 a 45-min App module | Both stages fit comfortably, but there's less time for the dashboard and Genie improvement story |

### Prerequisites (facilitator)

- Confirm that **Genie Code** and **Databricks Apps** are enabled in the workspace, and test both prompts end to end in the dry run (T-2 days).
- Pre-create the 5 apps (`t03-command-centre` and so on) the day before, with the SQL warehouse already added as an app resource. Teams then
  only change the code.
- Each app runs as its own **service principal**. Give it `USE CATALOG` on `<hack_catalog>` (facilitator), and `CAN USE` on the warehouse
  (through the app resource). The app is read-only, so teams grant only `SELECT` on their own schema:
  ```sql
  GRANT USE SCHEMA, SELECT ON SCHEMA <hack_catalog>.team_03 TO `<app-sp-application-id>`;
  ```
- Keep a working reference app (both tabs) in `starter-assets/` in case Genie Code gets stuck.

---

## 8. Challenge cards (one per team, all inside the Perfect Store Command Centre theme)

Each scenario has its own attendee instruction document in `scenarios/`:

| # | Team | Persona | Challenge | Suggested metric views | Document |
|---|---|---|---|---|---|
| A | 01 | **Supplier Account Manager** | "How is my brand performing vs the category and vs budget, and where am I losing share?" | `mv_sales`, `mv_budget` | `scenarios/A-supplier-account-manager.md` |
| B | 02 | **Field Operations Manager** | "Which stores and reps drive the best OSA and compliance, and where should reps go next week?" | `mv_execution`, `mv_sales` | `scenarios/B-field-operations-manager.md` |
| C | 03 | **Trade Marketing Manager** | "Which promotions actually deliver profitable uplift?" | `mv_sales`, `mv_promo` | `scenarios/C-trade-marketing-manager.md` |
| D | 04 | **Client Executive** | "One-page Monday business overview, with drill-downs for 'why?'" | `mv_sales`, `mv_budget`, `mv_execution` | `scenarios/D-client-executive.md` |
| E | 05 | **Insights Analyst** | "What do merchandisers say in visit notes, and how does it link to OSA and sales?" (AI Functions from the start) | `mv_notes`, `mv_execution` | `scenarios/E-insights-analyst.md` |

Each card comes with **10 Genie test questions** with expected answers, including 3–4 "trap" questions that need tuning to answer correctly.

### Minimum vs stretch

| Area | Minimum (must have) | Stretch (bonus points) |
|---|---|---|
| Dashboard | v1 on tables, then v2 on metric views: 2 pages, at least 6 visuals, global filters, published | Drill-through, scheduled subscription, Genie embedded in the dashboard |
| Metric views | 1 metric view with at least 4 measures, including one ratio | 2 or more metric views, YoY and filtered measures, synonyms and display names |
| Genie | Baseline score, then instructions + sample questions + metric view added, with the final score recorded | SQL expressions, example SQL, trusted functions, benchmarks run |
| App (optional) | — | Stage 1: deployed app with a filterable data table (Tab 1). Stage 2: visuals tab (Tab 2). Bonus: Genie chat tab |

---

## 9. Workspace pre-requisites (agree with the customer admin)

| # | Item | Owner | When |
|---|---|---|---|
| 1 | Confirm the region supports **Serverless SQL**, **Genie**, **Metric Views**, **Foundation Model APIs** (AI Functions) and, if the App track is used, **Databricks Apps** | Databricks | T-2 weeks |
| 2 | Turn on **partner-powered AI features** and the Databricks Assistant | Customer admin | T-2 weeks |
| 3 | Create the catalog `<hack_catalog>` (with a managed storage location if the metastore has no default) | Customer admin | T-2 weeks |
| 4 | Create the account group `<hackathon_participants>` (20 users) and the `team_01`…`team_05` groups | Customer admin | T-1 week |
| 5 | Make the facilitator the owner of `<hack_catalog>`, and give participants `USE CATALOG` + `CREATE SCHEMA` on it | Customer admin | T-1 week |
| 6 | Create **2 serverless SQL warehouses** (Medium, autoscale 1–3), with `CAN USE` for the participants | Customer admin / facilitator | T-1 week |
| 7 | *(App track only)* Confirm Genie Code and Apps are enabled, the app quota is ≥ 10, and the 5 apps are pre-created | Customer admin / facilitator | T-1 week |
| 8 | Load `hack_14oct` and `facilitator_kit`, run the grant script, and smoke-test as a non-admin user | Facilitator | T-3 days |
| 9 | Dry run as a test participant through every sprint, then drop the test schema | Facilitator | T-2 days |
| 10 | Make sure every user can log in (SSO/MFA) to the workspace URL | Customer | T-1 day |

### Grant script (run once by the facilitator)

```sql
-- Catalog: everyone can enter it and create their team schema
GRANT USE CATALOG, CREATE SCHEMA ON CATALOG <hack_catalog> TO `<hackathon_participants>`;

-- Source schema: read-only for participants
GRANT USE SCHEMA, SELECT ON SCHEMA <hack_catalog>.hack_14oct TO `<hackathon_participants>`;

-- facilitator_kit: no grants to participants (answer keys)
```

Team schemas need **no facilitator grants**, because each team owns its schema. Teams can share their work with everyone for the demos:
`GRANT USE SCHEMA, SELECT ON SCHEMA <hack_catalog>.team_03 TO \`<hackathon_participants>\`;`

> **Guardrail:** `CREATE SCHEMA` on the catalog means anyone *could* create extra schemas. The convention is `team_XX` only, and the
> facilitator checks `SHOW SCHEMAS IN <hack_catalog>` after Sprint 0. For tighter control, the facilitator pre-creates the 5 empty
> schemas owned by the team groups, and teams only run the copy part of the script.

---

## 10. Facilitator kit (prepare in this folder)

```
databricks-aibi-hackathon/
├── hackathon-plan.md              ← this file
├── notebooks/                     ← import into your workspace (keep docs/ next to them)
│   ├── 00_facilitator_runbook     ← ✅ created: step-by-step setup and test, including Step 3 synthetic data as Delta tables in hack_14oct
│   ├── 01_team_setup              ← ✅ created: teams copy every table from hack_14oct to team_XX
│   └── 02_apply_reference_descriptions ← ✅ created: fallback that applies the answer-key descriptions to a team schema
│       (grants, answer-key build, metric view reference and smoke tests are all steps inside 00_facilitator_runbook)
├── attendee-guide.md              ← ✅ created: login, naming, sprint-by-sprint steps, cheat-sheets, Genie Code prompts
├── scenarios/                     ← ✅ created: one attendee instruction document per scenario (A–E)
├── genie-test-answers.md          ← facilitator only: expected answers and SQL for the 10 questions per scenario (also used as benchmarks)
├── scoreboard.md / sheet          ← Genie baseline → final per team
├── starter-assets/                ← fallback dashboard JSON, Genie space config, (optional) reference 2-tab app
└── judging-rubric.md
```

**Staffing:** 1 lead facilitator and 1–2 floating helpers (about 1 helper per 2 teams). One of them owns the scoreboard and, if the App track runs, the app SP grants.

---

## 11. Judging rubric (100 points, +10 bonus)

| Criterion | Points |
|---|---|
| Business value and storytelling (clear persona, insight, and action) | 20 |
| Dashboard quality (v2: clarity, interactivity, correctness) | 15 |
| Metric views (coverage, correct ratio/YoY measures, metadata, reused in the dashboard and Genie) | 15 |
| **Data descriptions** (coverage and quality of table and column descriptions compared with the answer key, tags) | 15 |
| Genie: final accuracy on the test questions | 15 |
| Genie: **improvement** from baseline to final, and the tuning techniques used | 10 |
| Creativity and use of AI features (AI Functions, AI-assisted authoring) | 10 |
| **Bonus:** Databricks App (optional track): Stage 1 table (+5), Stage 2 visuals (+5) | +10 |

---

## 12. Compute and cost guardrails

- 2 serverless SQL warehouses (Medium, auto-stop 10 minutes). Teams 1–3 use warehouse A and teams 4–5 use warehouse B.
- Fact table of at most around 5M rows, so queries return in seconds.
- *(App track)* At most 1 app per team, and stop all apps at the end of the day.
- Optional: set a budget policy or tag (`project=hackathon`) to track spend.
- Everything is serverless, so there are no clusters to configure.

---

## 13. Risks and mitigations

| Risk | Mitigation |
|---|---|
| A feature isn't enabled (Genie, Metric Views, FMAPI, Apps) | Validate at T-2 weeks, and do the dry run as a non-admin user |
| Users can't log in or lack entitlements | Login check at T-1 day, and one spare test account |
| Teams fall behind a checkpoint | Starter assets in `facilitator_kit` for every sprint |
| Metric view YAML errors slow teams down | A working template in the guide, the UI-based route plus the Assistant, and the reference view as a fallback |
| Genie baseline is already "too good" (no visible improvement) | Leave `hack_14oct` undocumented, use business abbreviations in column names, and plant ambiguous "trap" questions and fiscal-calendar rules in the test set |
| AI-generated descriptions are accepted without review, so they're plausible but wrong | The business SME on each team reviews them, the answer key is used for scoring, and the scoreboard shows whether descriptions actually helped |
| A team runs out of time in Sprint 4a | The facilitator gives it a script that applies the answer-key descriptions for the remaining tables |
| A team breaks its data | Re-run `01_team_setup`. `hack_14oct` is read-only |
| Extra or oddly named schemas | Naming convention, and a facilitator check after Sprint 0 |
| *(App track)* The app SP has no access | Pre-created apps, with the SP given `USE CATALOG` and warehouse access in advance; teams grant schema access themselves |

---

## 14. Post-hackathon and open decisions

**Post-hackathon**
- Share the winning assets, and keep the best metric views, dashboard and Genie space as a reference.
- Cleanup: drop the team schemas (or the catalog), stop or delete any apps, and remove the groups. **Agree with the customer what to keep before deleting anything.**
- Follow-up: pick 1–2 real use cases from the challenge cards for a POC on the customer's real data, starting with metric views as the semantic layer.

**Open decisions to confirm with the customer**
1. Catalog name, and whether a new catalog can be created (or which existing one to use).
2. ~~Theme~~: **locked:** Perfect Store Command Centre.
3. Whether the App track is in scope (stretch or full module). Genie Code builds the app, and Streamlit is the suggested framework.
4. Team composition (5×4 is recommended), and whether participants are business, technical, or mixed users.
5. Data: prepared by the facilitator before the hackathon (fictional names, following the data contract in section 3.1).
6. Prizes and judges (ideally a customer business sponsor on the panel).
