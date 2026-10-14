# Databricks Hackathon: Perfect Store Command Centre

**AI/BI Dashboards · Metric Views · Genie · Databricks Apps**

**Format:** 4 hours, in person, hands-on · **Participants:** 20 (each working individually) · **Workspace:** customer-provided, Unity Catalog enabled, no data yet

> Names in `<angle brackets>` are placeholders to confirm with the customer
> (catalog name, group names, warehouse name).

---

## 1. Goals and approach

### Approach: "quick win first, then make it better"

Every module follows the same rhythm, so attendees get results within minutes and then learn *why* the governed way is better:

```
 QUICK WIN (≈25 min)                      IMPROVE (≈35 min)                         SEE THE DIFFERENCE
 ─────────────────────                    ─────────────────────                     ──────────────
 Dashboard straight on the attendee tables →  Rebuild on METRIC VIEWS (one definition →  Same numbers everywhere,
 using AI-assisted widgets                of Sales, Margin %, YoY, OSA %)            and less SQL per widget

 Genie space on the undocumented tables, →  1) DESCRIBE THE DATA in UC (table and    →  Re-ask the same 10
 asking 10 questions                        column descriptions, AI-generated then      questions and compare
                                            reviewed)                                   the answers
                                            2) instructions, sample questions, SQL
                                            expressions, metric views
```

### Outcomes: by the end, each attendee has

| # | Deliverable | Status |
|---|---|---|
| 1 | An **AI/BI Dashboard**: a quick version first, then rebuilt on metric views | **Core** |
| 2 | One or more **UC Metric Views** that define the attendee's business KPIs once | **Core** |
| 3 | **Documented data:** table and column descriptions on every table in the attendee schema, AI-generated and then reviewed by the attendee | **Core (key capability)** |
| 4 | A **Genie space**, tuned with descriptions, instructions, sample questions and metric views | **Core** |
| 5 | A **Databricks App** built with Genie Code: Tab 1 shows a data table, Tab 2 shows visuals | **Core** (section 7) |
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

There is **one scenario for everyone** (section 8, in `attendees/01_instructions.md`): no options and no roles. Every attendee builds the same thing with the same data.

---

## 2. Data strategy: one catalog, one source schema, a schema per attendee

### Decision

**One catalog for the whole hackathon, with one read-only source schema. Each attendee creates their own schema and copies the data into it.**

```
<hack_catalog>                          one catalog for the whole event
├── hack_14oct         (READ-ONLY)     ← facilitator loads the sample data here (single source of truth), with minimal descriptions on purpose
│     ├── dim_* / fact_* tables
│     └── visit_notes
├── jane_doe           (OWNED BY ATTENDEE) ← created by each attendee on the day; data copied from hack_14oct
├── john_smith
├── ...
└── (one schema per attendee, 20 in total)
```

**How it works**

1. The facilitator fills in **one config file** (`hack_setup/config.yaml`: catalog, warehouse ID, attendee names and emails) and clicks **Run all** on `hack_setup/00_facilitator_runbook`.
   It builds `hack_14oct` (**read-only** for attendees), grants access, and **creates one schema per attendee**, named after them, with a copy
   of every table, **owned by the attendee** (section 3.2).
2. In Sprint 0, each attendee opens their schema in Catalog Explorer and reads the hints in the attendee instructions.
3. From then on, attendees work **only in their own schema**. Their dashboards, metric views, Genie space and app all point at it.
4. Attendees **own the metadata** of their copy. They write the table and column descriptions themselves (section 5), and can change
   the copy freely (add columns, views, metric views, write-back) without affecting anyone else.

**Why this model works**

| Benefit | Detail |
|---|---|
| Simple to administer | One config file, one catalog, one data load. One **Run all** does the data, the grants and the attendee schemas |
| Attendees own their data **and its descriptions** | They can `COMMENT ON` tables and columns, accept AI-generated descriptions, `ALTER`, create metric views and write back without asking for grants. **This is why we copy instead of sharing one schema** |
| Safe | `hack_14oct` is read-only. If an attendee breaks their data, the facilitator drops their schema and runs the setup notebook again |
| Attendees grant their own app's access | Each attendee owns their schema, so they can grant their app's service principal access themselves |
| Shows Unity Catalog in action | Ownership, grants, lineage (`hack_14oct` → `<attendee_schema>` → metric view → dashboard/Genie), cloning |
| Easy cleanup | `DROP SCHEMA <hack_catalog>.<attendee_schema> CASCADE`, or drop the whole catalog |

**Trade-offs to manage**

- **Storage:** 5 copies. At about 5M rows that's small (a few hundred MB at most).
- **Drift:** attendees' numbers can differ after their changes. That's fine, because each attendee works with their own copy.
- **Constraints:** the copy script re-applies the PK/FK constraints, because Genie uses them for joins. Descriptions are deliberately left for the attendees to write.

### Working individually

- **20 attendees, each on their own**, each in their own schema. There are no attendees.
- **Everyone does the same scenario** (section 8). No options, no special roles.
- **Schema naming:** the setup notebook names each schema after the attendee's name in `config.yaml` (`Jane Doe` → `jane_doe`).
- **Ownership:** whoever creates the schema owns it, so no ownership transfer is needed.
- **Asset naming:** start with the attendee's initials: dashboard `JD – Trade Performance`, Genie space `JD – Trade Genie`, app `jd-command-centre`. Metric views go in the attendee's schema (`jane_doe.mv_sales`).

### Fallback (if the customer can't create a new catalog)

Use one existing catalog that the customer assigns, and create `hack_14oct` and the attendee schemas inside it. Nothing else changes.

---

## 3. Sample data design

> **Status:** the data is **synthetic and generated** by the `01_generate_synthetic_data` notebook, which Step 3 of
> `00_facilitator_runbook` calls. It writes the tables below **directly as Delta tables** in `hack_14oct`. The same run then copies them
> into every attendee's own schema (Step 6).
> The attendee instructions, metric view template, Genie test questions and app prompts refer to these table and column names.

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

**Data checklist (facilitator, before T-3 days):** fill in `config.yaml`, click **Run all** on the setup notebook, and check the Step 7 summary.

### 3.1a Description strategy: undocumented on purpose

Writing descriptions is a **key capability to showcase**, so the `hack_14oct` tables ship **almost undocumented**:

| Where | What it contains | Why |
|---|---|---|
| `hack_14oct.*` (what attendees copy) | **No descriptions and no metric views.** Cryptic, inconsistent column names (`str_id`, `sku`, `qty`, `nsv`, `gp`, `prm_flg`, `wk_strt_dt`, `rgn`, `fmt_cd`, `osa_pct`, `nt_txt`) and coded values (`fmt_cd` HYP/SUP/CNV/WHS, `sts` O/C, `prm_typ` PR/MB/BN) | Like real source systems. Dashboards and Genie must guess until attendees describe the data and build metric views, which gives a clear baseline |

Attendees ask Genie the same questions before and after describing the data, and see the difference (section 5).

### 3.2 Attendee schemas (created by the facilitator from the config file)

Runbook **Step 6** reads the attendee list from `hack_setup/config.yaml` and, for each attendee:

```sql
-- 1. Create the attendee's schema, named after their NAME (Jane Doe -> jane_doe). Existing schemas are left alone.
CREATE SCHEMA <catalog>.jane_doe COMMENT 'Perfect Store hackathon: working schema of jane.doe@…, copied from hack_14oct';

-- 2. Copy every source table (DEEP CLONE = an independent copy), and add the PK/FK constraints
CREATE OR REPLACE TABLE <catalog>.jane_doe.fact_sales_weekly DEEP CLONE <catalog>.hack_14oct.fact_sales_weekly;
-- ... the same for every dim_* / fact_* / visit_notes table

-- 3. Make the attendee the owner of every table and of the schema
ALTER TABLE <catalog>.jane_doe.fact_sales_weekly OWNER TO `jane.doe@…`;
ALTER SCHEMA <catalog>.jane_doe OWNER TO `jane.doe@…`;
```

Someone who wasn't in the config file? Add them to `config.yaml` and run the setup notebook again: existing schemas aren't touched.


> Metric views and descriptions are **not** pre-built in attendee schemas. Building them is the hackathon exercise (Sprints 2 and 4).

| Copy method | Pros | Cons | Use it |
|---|---|---|---|
| `DEEP CLONE` | Independent copy, keeps comments and properties, safe to change | Copies the storage (small here) | **Default** |
| `SHALLOW CLONE` | Instant, and no data is copied | Depends on the source files, so attendee tables can break if the source is rebuilt | Only if the data is very large |
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
| Different attendees get different numbers | One governed definition, with lineage in Catalog Explorer |

### Exercise ladder (Sprint 2)

| Level | Task | Outcome |
|---|---|---|
| **L1: First metric view** | `mv_sales` on `fact_sales_weekly` joined to `dim_store`, `dim_product` and `dim_date`. Measures: Sales, Units, Margin, **Margin %** | Query it with `SELECT Region, MEASURE(Sales) ... GROUP BY ALL` |
| **L2: Business measures** | Add **YoY growth %**, **Avg selling price**, **Promo sales share %**, plus filtered measures (for example `Sales on promo`) | Measures that would take complicated SQL in every widget |
| **L3: More subject areas** | `mv_execution` on `fact_store_visits` (OSA %, compliance %, visits per store), and `mv_budget` (Budget, Actual, Variance %) | One metric view per business domain |
| **L4: Make it discoverable** | Add comments, display names and synonyms to the measures and dimensions | Genie and dashboard users understand the fields |
| **L5: Reuse it** | Switch the dashboard datasets to the metric views, and add the metric views to the Genie space | The before/after comparison for the demo |

Attendees get a partly filled metric view starter with TODOs in the attendee instructions (Appendix A).

> Attendees can also build metric views in the **Catalog Explorer UI** (with the Assistant's help) instead of writing YAML. Both routes are valid.

---

## 5. Genie: quick win, describe the data, then tune

### Quick win (Sprint 3)

1. Create a Genie space on the attendee's tables as they are: **undocumented** (`fact_sales_weekly`, the dims, and `fact_store_visits`).
2. Ask the **10 questions** from the attendee instructions (Sprint 3), and note which answers look wrong or unclear.

### Sprint 4a: describe your data in Unity Catalog (key capability)

Each attendee owns their schema, so they can document every table and column themselves. **The descriptions are written once in Unity Catalog and
then used everywhere:** by Genie, the Databricks Assistant, AI-assisted dashboard authoring, metric views, and search in Catalog Explorer.

| Step | How | Tip |
|---|---|---|
| **1. AI-generated table descriptions** | Catalog Explorer → table → **Overview** → *AI generate* the description → review → **Accept** or edit | AI gives a first draft. The attendee reviews it and makes it correct |
| **2. AI-generated column descriptions** | Catalog Explorer → **Columns** tab → AI-suggested descriptions → accept or edit each one | Concentrate on the columns behind the 10 questions and the abbreviations (`nsv`, `osa_pct`, `fy_wk`) |
| **3. Fix them in SQL (faster in bulk)** | `COMMENT ON TABLE jane_doe.fact_sales_weekly IS '...';` and `ALTER TABLE jane_doe.fact_sales_weekly ALTER COLUMN nsv COMMENT 'Net sales value in ZAR, excl. VAT';` | Ask the Assistant to draft the statements for a whole table |
| **4. Tags** | Add governed tags such as `domain=sales`, `kpi=true`, `pii=false` | Shows governance and makes data easier to find |
| **5. Re-ask Genie** | Ask the same 10 questions again, **without changing anything else** | Compare the answers. This shows the value of good metadata |

**What a good description includes** (on the attendee instructions cheat-sheet): the business meaning, the **unit and currency**, the **grain**
("one row per store, SKU and week"), allowed values or codes, **abbreviations spelled out**, and common synonyms ("OSA, availability, in-stock").


### Sprint 4b: Genie tuning ladder. Each step should improve the answers

| Level | What to add | Example | Typical fix |
|---|---|---|---|
| **G1: General instructions** | Business rules in plain language | "Sales means net sales value excl. VAT. The fiscal year starts in March. 'Top' means by sales unless stated. Show currency in ZAR" | Ambiguous terms, fiscal periods |
| **G2: Space-level refinements** | On top of the UC descriptions from 4a: add column synonyms in the space, hide irrelevant columns, and add example values | `osa_pct` synonyms: "OSA", "availability", "in-stock" | Wrong column chosen |
| **G3: Sample questions** | 5–8 starter questions shown to users | "Which regions are below budget this fiscal quarter?" | Users get started quickly |
| **G4: SQL expressions** | Reusable measures, filters and dimensions in the space's knowledge store | Filter `Active stores = store_status = 'Open'`, measure `Margin %` | Repeated logic gets defined once |
| **G5: Joins and example SQL** | Define join relationships, and add example SQL queries for the hard questions | YoY growth, share of category | Wrong joins, complex calculations |
| **G6: Metric views as data** | Add `mv_sales`, `mv_execution` and `mv_budget` to the space (alongside the tables or instead of them) | Genie uses `MEASURE(\`Margin %\`)` | The governed KPIs come along for free |
| **G7: Trusted assets** | UC SQL functions for parameterised business questions | `fn_store_summary(str_id)` | Answers marked as trusted |

---

## 6. Agenda (4 hours)

| Time | Sprint | Content | Checkpoint |
|---|---|---|---|
| 0:00 – 0:15 | **Kick-off** | Goals, the "quick win then improve" approach, the **Perfect Store Command Centre** storyline, rules, and the scenario | Ready |
| 0:15 – 0:30 | **Sprint 0: Attendee setup** | Check your pre-created schema in Catalog Explorer, then a quick Catalog Explorer tour (lineage, ownership, and notice that the tables have **no descriptions** yet) | Team schema ready |
| 0:30 – 1:00 | **Sprint 1: Dashboard quick win** | 5 min demo, then 25 min build: a dashboard straight on the attendee tables, using the AI assistant to create widgets, plus filters, then publish | **First dashboard published** |
| 1:00 – 1:45 | **Sprint 2: Metric views** | 10 min demo, then 35 min build: metric view ladder L1–L5, and switch the dashboard to the metric views | **Dashboard v2 on metric views** |
| 1:45 – 1:55 | Break | | |
| 1:55 – 2:20 | **Sprint 3: Genie quick win** | 5 min demo, then 20 min build: a Genie space on the undocumented tables, with the 10 test questions | **Genie space created** |
| 2:20 – 2:40 | **Sprint 4a: Describe your data** | 5 min demo, then 15 min build: AI-generated table and column descriptions, reviewed and edited by the attendee, then the same questions re-asked | **Tables described** |
| 2:40 – 3:10 | **Sprint 4b: Genie tuning** | 5 min demo, then 25 min build: tuning ladder G1–G7, including adding the metric views | **Genie tuned** |
| 3:10 – 3:30 | **Sprint 5: App** | 5 min demo, then 15 min build with Genie Code: Tab 1 data table (deploy), then Tab 2 visuals (section 7) | **App deployed** |
| 3:30 – 3:55 | **Demos** | 5 volunteers × 4 min: show **before → after** (dashboard v1 → v2, Genie answers before and after tuning) | |
| 3:55 – 4:00 | **Wrap-up** | Next steps, survey | |

> **Nobody gets stuck:** if an attendee misses a checkpoint, a helper sits with them and they carry on with the next sprint.

---

## 7. Databricks App (2 stages, built with Genie Code)

Everyone builds the app in Sprint 5. Confirm at T-2 weeks that the workspace supports Databricks Apps and Genie Code.
Attendees **don't write the app by hand**. They describe what they want to **Genie Code** (the AI coding agent in the workspace), then
review and deploy what it builds. The app has two tabs, built one stage at a time:

```
 ┌──────────────────────────────────────────────────────────────┐
 │  JD Command Centre                                           │
 │  [ Tab 1: Data ]  [ Tab 2: Insights ]                        │
 ├──────────────────────────────────────────────────────────────┤
 │  Stage 1 → Tab 1: filterable TABLE of the attendee's data        │
 │  Stage 2 → Tab 2: VISUALS (KPI tiles + charts), same filters │
 └──────────────────────────────────────────────────────────────┘
```

### Stage 1: Tab 1 "Data", a table (≈10 min)

| | |
|---|---|
| **Goal** | A deployed app with one tab that shows a filterable table from the attendee's **metric view** (or tables) |
| **Data** | `<attendee_schema>.mv_sales`, queried with `MEASURE()`, through the SQL warehouse attached as an app resource |
| **Done when** | The app URL opens, the table loads, and the filters (Region, Retailer, Category, Week range) work |

**Starter prompt for Genie Code:**
> Build a Streamlit Databricks App called "T03 Command Centre" with two tabs: "Data" and "Insights". Leave "Insights" empty for now.
> On the "Data" tab, query `<hack_catalog>.jane_doe.mv_sales` through the SQL warehouse app resource, using `MEASURE()` for
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

### Tips for attendees

- **Iterate in small prompts:** "make the table paginated", "add a download-as-CSV button", "show a Margin % below 20% in red".
- **Use the metric views.** The app then shows exactly the same numbers as the dashboard and Genie, which is a good demo point.
- **Keep the app's start command and port as Genie Code or the template set them.** The app must listen on the port the platform gives it,
  or it shows as running but won't load.

### Prerequisites (facilitator)

- Confirm that **Genie Code** and **Databricks Apps** are enabled in the workspace, and test both prompts end to end in the dry run (T-2 days).
- Each attendee creates their own app (`jd-command-centre`), adding the SQL warehouse as an app resource. **Check the workspace app quota (20+)**,
  or pre-create the apps the day before so attendees only change the code.
- Each app runs as its own **service principal**. Give it `USE CATALOG` on `<hack_catalog>` (facilitator), and `CAN USE` on the warehouse
  (through the app resource). The app is read-only, so attendees grant only `SELECT` on their own schema:
  ```sql
  GRANT USE SCHEMA, SELECT ON SCHEMA <hack_catalog>.jane_doe TO `<app-sp-application-id>`;
  ```

---

## 8. The scenario (the same for everyone)

**Monday Command Centre** (all in `attendees/01_instructions.md`): *"How did we sell? Are we on budget? What is happening on the shelf?"*

| Part | What everyone builds |
|---|---|
| Dashboard | v1 on the tables, then v2 on metric views: an executive page plus a "Why?" drill-down page. **Bonus:** a custom visual (bullet chart of Sales vs Budget by region) with Custom Viz (Vega-Lite, Public Preview) |
| Metric views | `mv_sales` (Sales, Units, Margin, Margin %, YoY, Promo Sales), `mv_budget` (Budget, Variance %), `mv_execution` (Avg OSA %, POG compliance %, % of stores below target) |
| Descriptions | Every table and column in their schema, AI-generated and then reviewed |
| Genie | 10 questions, re-asked after describing the data and after tuning |
| App | Tab 1 data table and Tab 2 visuals, built with Genie Code |

The 10 Genie questions include 3–4 tricky ones (sales = NSV, fiscal year March–February, "last week", the OSA target)
that Genie only handles well after the data is described and the space is tuned.

---

## 9. Workspace pre-requisites (agree with the customer admin)

| # | Item | Owner | When |
|---|---|---|---|
| 1 | Confirm the region supports **Serverless SQL**, **Genie**, **Metric Views**, **Foundation Model APIs** and **Databricks Apps**, plus **Custom Viz** in AI/BI dashboards (Public Preview, for the bonus custom visual) | Databricks | T-2 weeks |
| 2 | Turn on **partner-powered AI features** and the Databricks Assistant | Customer admin | T-2 weeks |
| 3 | Create the catalog `<hack_catalog>` (with a managed storage location if the metastore has no default) | Customer admin | T-2 weeks |
| 4 | Create the account group `<hackathon_participants>` (20 users) | Customer admin | T-1 week |
| 5 | Make the facilitator the owner of `<hack_catalog>` (the runbook then grants attendees `USE CATALOG` from the config file) | Customer admin | T-1 week |
| 6 | Create **2 serverless SQL warehouses** (Medium, autoscale 1–3), with `CAN USE` for the participants | Customer admin / facilitator | T-1 week |
| 7 | Confirm Genie Code and Apps are enabled and the app quota is ≥ 20 (or pre-create the apps) | Customer admin / facilitator | T-1 week |
| 8 | Run the setup notebook (data, grants, attendee schemas), and test as an attendee (non-admin user) | Facilitator | T-3 days |
| 9 | Dry run as a test participant through every sprint, then drop the test schema | Facilitator | T-2 days |
| 10 | Make sure every user can log in (SSO/MFA) to the workspace URL | Customer | T-1 day |

### Grants (done by runbook Step 5, from the config file)

For every attendee in `hack_setup/config.yaml`, the runbook grants to their email:

```sql
GRANT USE CATALOG ON CATALOG <hack_catalog> TO `jane.doe@…`;                 -- enter the catalog (no CREATE SCHEMA needed)
GRANT USE SCHEMA, SELECT ON SCHEMA <hack_catalog>.hack_14oct TO `jane.doe@…`;   -- read-only source
-- plus CAN USE on the SQL warehouse from config.yaml (through the Databricks SDK)
```

Attendees own their schema, so they need no other grants on it. To show their work in the demos, an attendee can run
`GRANT USE SCHEMA, SELECT ON SCHEMA <hack_catalog>.jane_doe TO \`<hackathon_participants>\`;`

---

## 10. Materials

```
databricks-aibi-hackathon/
├── README.md
├── .gitignore                     ← keeps hack_setup/config.yaml (real emails and IDs) out of the repo
├── attendees/                     ← instructions only (share with attendees)
│   └── 01_instructions.md         ← the hackathon, sprint by sprint (a future 02_… file can hold advanced scenarios)
├── docs/
│   └── hackathon-plan.md          ← facilitator plan (this file)
└── hack_setup/                    ← facilitator only: everything to set up the hackathon
    ├── config.example.yaml        ← copy to config.yaml: catalog, warehouse ID, attendee names and emails
    ├── 00_facilitator_runbook     ← Run all: hack_14oct + synthetic data + constraints + grants + one schema per attendee
    └── 01_generate_synthetic_data ← synthetic data generator (called by the runbook)
```


**Staffing:** 1 lead facilitator and 2 floating helpers (about 1 helper per 10 attendees). One of them handles the app SP grants.

---

## 11. Compute and cost guardrails

- 1–2 serverless SQL warehouses (Medium, autoscale, auto-stop 10 minutes) for 20 attendees.
- About 350K weekly sales rows, so queries return in seconds.
- At most 1 app per attendee (check the workspace app quota), and stop all apps at the end of the day.
- Optional: set a budget policy or tag (`project=hackathon`) to track spend.
- Everything is serverless, so there are no clusters to configure.

---

## 12. Risks and mitigations

| Risk | Mitigation |
|---|---|
| A feature isn't enabled (Genie, Metric Views, FMAPI, Apps) | Validate at T-2 weeks, and do the dry run as a non-admin user |
| Users can't log in or lack entitlements | Login check at T-1 day, and one spare test account |
| Attendees fall behind a checkpoint | Helpers sit with them, and they carry on with the next sprint |
| Metric view YAML errors slow attendees down | The partly filled starter in the guide, the UI-based route, and the Assistant |
| Genie already answers well before tuning (no visible improvement) | Leave `hack_14oct` undocumented, use business abbreviations in column names, and plant ambiguous "trap" questions and fiscal-calendar rules in the test set |
| AI-generated descriptions are accepted without review, so they're plausible but wrong | Each attendee reviews them, and re-asking the questions shows whether descriptions actually helped |
| An attendee breaks their data | Drop their schema and run the setup notebook again. `hack_14oct` is read-only |
| Extra or oddly named schemas | Naming convention, and a facilitator check after Sprint 0 |
| The app SP has no access | Pre-created apps, with the SP given `USE CATALOG` and warehouse access in advance; attendees grant schema access themselves |

---

## 13. Post-hackathon and open decisions

**Post-hackathon**
- Share the winning assets, and keep the best metric views, dashboard and Genie space as a reference.
- Cleanup: drop the attendee schemas (or the catalog), stop or delete any apps, and remove the groups. **Agree with the customer what to keep before deleting anything.**
- Follow-up: pick 1–2 real use cases from the scenario for a POC on the customer's real data, starting with metric views as the semantic layer.

**Open decisions to confirm with the customer**
1. Catalog name, and whether a new catalog can be created (or which existing one to use).
2. ~~Theme~~: **locked:** Perfect Store Command Centre.
3. Apps: confirm the app quota (20+). Genie Code builds the app, and Streamlit is the suggested framework.
4. Whether participants are business, technical, or mixed users.
5. Data: prepared by the facilitator before the hackathon (fictional names, following the data contract in section 3.1).
