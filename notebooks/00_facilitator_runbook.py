# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Facilitator runbook: Perfect Store Command Centre hackathon
# MAGIC
# MAGIC **AI/BI Dashboards · Metric Views · Genie · Databricks Apps (optional)**
# MAGIC
# MAGIC This notebook walks you **step by step** through preparing and testing the hackathon environment. Run it **one section at a time**,
# MAGIC top to bottom. Don't use *Run all*. Each step says what it does, whether it changes anything, and what "done" looks like.
# MAGIC
# MAGIC | Step | What | Changes anything? |
# MAGIC |---|---|---|
# MAGIC | 0 | Configure (catalog widget, fixed settings) | No |
# MAGIC | 1 | Pre-flight checks (identity, catalog, warehouses, AI Functions, Apps) | No |
# MAGIC | 2 | Create the source and facilitator-kit schemas | **Yes** |
# MAGIC | 3 | **Create the data:** generate the synthetic dataset as Delta tables in `hack_14oct`, then check the data contract | **Yes** |
# MAGIC | 4 | Check the description strategy (the source should be almost undocumented) | Optional |
# MAGIC | 5 | Add PK/FK constraints to the source tables | **Yes** |
# MAGIC | 6 | Build the facilitator kit: clone, reference descriptions, reference metric views | **Yes** |
# MAGIC | 7 | Grant permissions to participants | **Yes** |
# MAGIC | 8 | **Test as an attendee:** open `01_team_setup` yourself (it copies every table from `hack_14oct` into a team schema), then test every sprint | Manual |
# MAGIC | 9 | Clean up the team schema you tested with | Manual |
# MAGIC
# MAGIC **Related notebooks in this folder:**
# MAGIC - `01_team_setup`: run by each team in Sprint 0. It creates `team_XX` and copies every table (with constraints) from the source schema into it.
# MAGIC - `02_apply_reference_descriptions`: a fallback if a team runs out of time in Sprint 4a.
# MAGIC - `03_generate_synthetic_data`: the synthetic data generator, called from Step 3.
# MAGIC
# MAGIC **Docs in this folder:** `docs/hackathon-plan.md`, `docs/attendee-guide.md`, `docs/scenarios/*.md`

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 0 · Configuration (placeholders)
# MAGIC
# MAGIC **Widgets (fill in at the top of the notebook):**
# MAGIC
# MAGIC | Widget | Meaning |
# MAGIC |---|---|
# MAGIC | `catalog` | The one catalog for the whole hackathon. **Required** |
# MAGIC | `participants_group` | The account group that contains all attendees. Leave blank while testing alone (Step 7 is then skipped) |
# MAGIC
# MAGIC **Fixed settings (variables in the next cell; edit there only if needed):**
# MAGIC
# MAGIC | Variable | Value | Meaning |
# MAGIC |---|---|---|
# MAGIC | `source_schema` | `hack_14oct` | The read-only source data schema that teams copy from |
# MAGIC | `kit_schema` | `facilitator_kit` | The facilitator-only answer key (described tables, reference metric views) |

# COMMAND ----------

dbutils.widgets.text("catalog", "<your_catalog>", "1. Catalog")
dbutils.widgets.text("participants_group", "", "2. Participants group (optional)")

# COMMAND ----------

catalog = dbutils.widgets.get("catalog").strip()
participants_group = dbutils.widgets.get("participants_group").strip()

# Fixed settings
source_schema = "hack_14oct"          # read-only source data (make it read-only for participants)
kit_schema = "facilitator_kit"        # facilitator-only answer key

def q(*parts):
    return ".".join(f"`{p}`" for p in parts)

def lit(text):
    return "'" + text.replace("\\", "\\\\").replace("'", "\\'") + "'"

isc = f"{q(catalog)}.information_schema"
SRC, KIT = q(catalog, source_schema), q(catalog, kit_schema)
print(f"Catalog      : {catalog}\nSource       : {SRC}\nKit          : {KIT}\nParticipants : {participants_group or '(not set: testing alone)'}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 · Pre-flight checks (read-only)
# MAGIC
# MAGIC **Done when:** you're who you expect, the catalog exists, at least one serverless SQL warehouse is available, and AI Functions return a result.

# COMMAND ----------

display(spark.sql("SELECT current_user() AS me, current_version().dbsql_version AS dbsql_version"))
cats = [r[0] for r in spark.sql("SHOW CATALOGS").collect()]
if catalog not in cats:
    raise ValueError(f"Catalog '{catalog}' not found (or you can't see it). Create it, or ask the admin: CREATE CATALOG `{catalog}`;")
print(f"✅ Catalog {catalog} exists")
display(spark.sql(f"SHOW GRANTS ON CATALOG {q(catalog)}"))

# COMMAND ----------

# SQL warehouses and Apps (read-only, via the SDK)
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

wh = [(x.name, x.id, str(x.state), x.cluster_size, bool(x.enable_serverless_compute)) for x in w.warehouses.list()]
display(spark.createDataFrame(wh, "name string, id string, state string, size string, serverless boolean") if wh else spark.createDataFrame([], "name string"))

try:
    apps = list(w.apps.list())
    print(f"✅ Databricks Apps API reachable: {len(apps)} app(s) in the workspace (check the quota if you're using the App track)")
except Exception as e:
    print(f"⚠️  Apps not available: {str(e)[:200]}")

# COMMAND ----------

# AI Functions (Foundation Model APIs). Needed for Scenario E and the AI Functions track.
display(spark.sql("""
    SELECT ai_classify('Shelf was empty, no stock of the 2L pack', ARRAY('out of stock', 'damaged display', 'other')) AS issue_type,
           ai_analyze_sentiment('Shelf was empty, no stock of the 2L pack') AS sentiment
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC **Manual pre-flight checklist** (tick these off in the UI):
# MAGIC - [ ] **Genie** is enabled (sidebar → Genie → *New* is available)
# MAGIC - [ ] **AI/BI Dashboards** with the AI assistant work (sidebar → Dashboards → Create)
# MAGIC - [ ] **Metric views** can be created (Catalog Explorer → schema → *Create* → *Metric view*)
# MAGIC - [ ] **AI-generated descriptions** are available in Catalog Explorer (table → *AI generate*)
# MAGIC - [ ] **Genie Code** opens in the app/notebook editor (App track only)
# MAGIC - [ ] Partner-powered AI features are enabled in the workspace/account settings

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 · Create the source and facilitator-kit schemas ⚠️ changes things
# MAGIC
# MAGIC Creates `source_schema` (where the data goes) and `kit_schema` (the answer key). Both are idempotent.
# MAGIC
# MAGIC > ⚠️ **Make the `hack_14oct` schema read-only for participants** (grant only `USE SCHEMA` and `SELECT`).
# MAGIC **Done when:** both schemas appear in Catalog Explorer.

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SRC} COMMENT 'Perfect Store hackathon: read-only source data. Teams copy from here.'")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {KIT} COMMENT 'Perfect Store hackathon: FACILITATOR ONLY answer key. Not granted to participants.'")
display(spark.sql(f"SHOW SCHEMAS IN {q(catalog)}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 · Create the data as Delta tables in `hack_14oct` ⚠️ changes things
# MAGIC
# MAGIC **3a** runs `03_generate_synthetic_data`, which writes a fully synthetic, fictional dataset **straight into Delta tables** in the source
# MAGIC schema (10 tables, about 350K weekly sales rows over 156 weeks, insights planted, **no descriptions and no metric views**). It takes a few minutes on serverless.
# MAGIC Re-running it overwrites the tables with the same data (fixed seed). **3b** checks the result.

# COMMAND ----------

# 3a · generate the synthetic dataset as Delta tables in the source schema
result = dbutils.notebook.run("./03_generate_synthetic_data", 3600, {"catalog": catalog})
print(result)
display(spark.sql(f"SHOW TABLES IN {SRC}"))

# COMMAND ----------

# MAGIC %md
# MAGIC **3b · Check the data contract (read-only).** This compares what's loaded with the contract that the attendee documents,
# MAGIC metric view template and app prompts use.
# MAGIC **Done when:** every table is ✅. A missing column is a ⚠️ warning. Either change the generator and re-run 3a, or update the
# MAGIC attendee docs and templates to match.

# COMMAND ----------

# Data contract: table -> columns the hackathon materials refer to (edit to match your final data)
DATA_CONTRACT = {
    "dim_date":            ["dt", "wk_strt_dt", "fy_cd", "fy_wk"],
    "dim_store":           ["str_id", "rgn", "rtl_grp", "fmt_cd", "prov"],
    "dim_product":         ["sku", "cat", "brnd", "supp_id", "rsp"],
    "dim_supplier":        ["supp_id", "supp_nm", "cat_typ"],
    "dim_merchandiser":    ["rep_id", "rep_nm"],
    "fact_sales_weekly":   ["wk_strt_dt", "str_id", "sku", "qty", "gsv", "nsv", "cogs", "gp", "prm_flg", "prm_id"],
    "fact_budget_monthly": ["mth_strt_dt", "rgn", "rtl_grp", "cat", "bgt_nsv"],
    "fact_promotions":     ["prm_id", "mech", "prm_typ", "disc", "sku", "rtl_grp", "strt_dt", "end_dt"],
    "fact_store_visits":   ["vst_id", "vst_dt", "str_id", "rep_id", "osa_pct", "pog_comp", "sos"],
    "visit_notes":         ["nt_id", "vst_id", "nt_txt"],
}

loaded = {}
for r in spark.sql(f"SELECT table_name, column_name FROM {isc}.columns WHERE table_schema = '{source_schema}'").collect():
    loaded.setdefault(r.table_name, set()).add(r.column_name)

report = []
for t, cols in DATA_CONTRACT.items():
    if t not in loaded:
        report.append((t, "❌ missing table", "", None))
        continue
    miss = [c for c in cols if c not in loaded[t]]
    n = spark.table(q(catalog, source_schema, t)).count()
    report.append((t, "✅" if not miss else "⚠️ columns missing", ", ".join(miss), n))
extra = sorted(set(loaded) - set(DATA_CONTRACT))
display(spark.createDataFrame(report, "table string, status string, missing_columns string, rows long"))
if extra:
    print(f"ℹ️  Extra tables in the source (they'll also be copied to the teams): {extra}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 · Description strategy: the source should be almost undocumented
# MAGIC
# MAGIC Writing descriptions is a **key capability** in Sprint 4a. Teams copy the source, so the source should have **no column descriptions**
# MAGIC (a one-line table comment at most). The cell below reports the coverage.
# MAGIC **Done when:** `pct_described` is about 0 for every source table.
# MAGIC
# MAGIC If your load added column comments, the **optional** cell after it removes them. It's guarded: set `STRIP = True` to run it.

# COMMAND ----------

display(spark.sql(f"""
    SELECT table_name, count(*) AS columns,
           count_if(comment IS NOT NULL AND trim(comment) <> '') AS described_columns,
           round(100 * count_if(comment IS NOT NULL AND trim(comment) <> '') / count(*), 0) AS pct_described
    FROM {isc}.columns WHERE table_schema = '{source_schema}'
    GROUP BY table_name ORDER BY table_name
"""))

# COMMAND ----------

STRIP = False   # ⚠️ set to True to remove all column comments from the SOURCE schema

if STRIP:
    for r in spark.sql(f"""SELECT table_name, column_name FROM {isc}.columns
                           WHERE table_schema = '{source_schema}' AND comment IS NOT NULL AND trim(comment) <> ''""").collect():
        spark.sql(f"ALTER TABLE {q(catalog, source_schema, r.table_name)} ALTER COLUMN `{r.column_name}` COMMENT ''")
    print("✅ Column comments removed from the source schema")
else:
    print("Skipped (STRIP = False)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5 · PK/FK constraints on the source tables ⚠️ changes things
# MAGIC
# MAGIC Genie uses informational PK/FK constraints to join tables correctly, and `01_team_setup` copies them to every team schema.
# MAGIC Edit the lists to match your data, then run. PK columns must be `NOT NULL` (the cell sets this).
# MAGIC **Done when:** the constraint listing at the end shows your PKs and FKs.

# COMMAND ----------

PRIMARY_KEYS = {          # table -> [pk columns]   (matches 03_generate_synthetic_data)
    "dim_date":          ["dt"],
    "dim_store":         ["str_id"],
    "dim_product":       ["sku"],
    "dim_supplier":      ["supp_id"],
    "dim_merchandiser":  ["rep_id"],
    "fact_promotions":   ["prm_id"],
    "fact_store_visits": ["vst_id"],
}
FOREIGN_KEYS = [          # (child table, [child cols], parent table, [parent cols])
    ("fact_sales_weekly", ["str_id"],     "dim_store",         ["str_id"]),
    ("fact_sales_weekly", ["sku"],        "dim_product",       ["sku"]),
    ("fact_sales_weekly", ["wk_strt_dt"], "dim_date",          ["dt"]),
    ("dim_product",       ["supp_id"],    "dim_supplier",      ["supp_id"]),
    ("fact_promotions",   ["sku"],        "dim_product",       ["sku"]),
    ("fact_store_visits", ["str_id"],     "dim_store",         ["str_id"]),
    ("fact_store_visits", ["rep_id"],     "dim_merchandiser",  ["rep_id"]),
    ("visit_notes",       ["vst_id"],     "fact_store_visits", ["vst_id"]),
]

def run(sql, label):
    try:
        spark.sql(sql); print(f"✅ {label}")
    except Exception as e:
        print(f"ℹ️  {label}: {str(e).splitlines()[0][:160]}")

for t, cols in PRIMARY_KEYS.items():
    for c in cols:
        run(f"ALTER TABLE {q(catalog, source_schema, t)} ALTER COLUMN `{c}` SET NOT NULL", f"NOT NULL {t}.{c}")
    run(f"ALTER TABLE {q(catalog, source_schema, t)} ADD CONSTRAINT `pk_{t}` PRIMARY KEY ({', '.join(f'`{c}`' for c in cols)})", f"PK {t}")

for child, ccols, parent, pcols in FOREIGN_KEYS:
    run(f"""ALTER TABLE {q(catalog, source_schema, child)} ADD CONSTRAINT `fk_{child}_{parent}`
            FOREIGN KEY ({', '.join(f'`{c}`' for c in ccols)}) REFERENCES {q(catalog, source_schema, parent)} ({', '.join(f'`{c}`' for c in pcols)})""",
        f"FK {child} → {parent}")

display(spark.sql(f"SELECT table_name, constraint_name, constraint_type FROM {isc}.table_constraints WHERE table_schema = '{source_schema}' ORDER BY 1, 3"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6 · Build the facilitator kit (answer key) ⚠️ changes things
# MAGIC
# MAGIC > **Optional, facilitator only.** The answer key lives only in `facilitator_kit`, never in `hack_14oct` or the team schemas, so
# MAGIC > attendees start with **no descriptions and no metric views** and build their own. Skip this step if you don't want an answer key
# MAGIC > (then `02_apply_reference_descriptions` has nothing to copy).
# MAGIC
# MAGIC **6a.** Clone every source table into the kit schema.
# MAGIC **6b.** Add **reference descriptions** to the kit tables. You can edit the dictionary below, *or* open each kit table in Catalog Explorer,
# MAGIC use **AI generate**, and correct the result. These are used to score teams, and by `02_apply_reference_descriptions`.
# MAGIC **6c.** Create the **reference metric views** (the answer key and fallback for Sprint 2).
# MAGIC
# MAGIC **Done when:** the kit tables are 100% described, and the reference metric view query returns rows.

# COMMAND ----------

# 6a · clone source -> kit
src_tables = [r.table_name for r in spark.sql(f"""SELECT table_name FROM {isc}.tables
    WHERE table_schema = '{source_schema}' AND table_type IN ('MANAGED','EXTERNAL') ORDER BY 1""").collect()]
for t in src_tables:
    spark.sql(f"CREATE OR REPLACE TABLE {q(catalog, kit_schema, t)} DEEP CLONE {q(catalog, source_schema, t)}")
    print(f"✅ kit.{t}")

# COMMAND ----------

# 6b · reference descriptions (edit or extend; columns that don't exist are skipped)
DESCRIPTIONS = {
    "dim_date": {
        "_table": "Calendar. One row per day, with calendar and fiscal attributes. The fiscal year runs 1 March to end of February.",
        "dt": "Calendar date. Primary key. Joins to fact_sales_weekly.wk_strt_dt (Mondays only).",
        "dt_key": "Date as an integer key in yyyyMMdd format.",
        "wk_strt_dt": "Monday that starts the week this date belongs to.",
        "cal_yr": "Calendar year.", "cal_q": "Calendar quarter (1–4).", "cal_mth": "Calendar month number (1–12).",
        "mth_nm": "Month name.", "dy_nm": "Day of the week name.", "wknd_flg": "True for Saturday and Sunday.",
        "fy_cd": "Fiscal year code, named after the year in which it ends (FY2027 = 1 Mar 2026 – 28 Feb 2027).",
        "fy_mth": "Fiscal month number (1 = March … 12 = February).",
        "fy_q": "Fiscal quarter (Q1 = March–May).",
        "fy_wk": "Fiscal week number (1–53). Week 1 starts on 1 March.",
    },
    "dim_store": {
        "_table": "Store master. One row per store, with the retailer group, format and South African geography.",
        "str_id": "Store identifier. Primary key.", "str_cd": "Store code used by the retailer.", "str_nm": "Store name.",
        "rtl_grp": "Retailer group (the retail chain the store belongs to). Also called retailer or chain.",
        "bnr": "Store banner (trading brand of the retailer group).",
        "fmt_cd": "Store format code: HYP = hypermarket, SUP = supermarket, CNV = convenience, WHS = wholesale / cash & carry.",
        "rgn": "Sales region (for example Gauteng North, KZN Inland). Also called region or area.",
        "prov": "South African province.", "cty": "City or town.", "lat": "Latitude.", "lng": "Longitude.",
        "opn_dt": "Date the store opened.", "sts": "Store status: O = open, C = closed.",
    },
    "dim_product": {
        "_table": "Product master. One row per SKU, with the category → subcategory → brand hierarchy.",
        "sku": "SKU (product) identifier. Primary key.", "sku_cd": "SKU code.", "sku_desc": "SKU description (brand, subcategory, pack size).",
        "brnd": "Brand name.", "supp_id": "Supplier identifier. Joins to dim_supplier.supp_id.",
        "cat": "Product category (top level of the hierarchy).", "sub_cat": "Product subcategory.",
        "pk_sz": "Pack size.", "rsp": "Recommended selling price per unit in ZAR excl. VAT (list price at the start of the history).",
    },
    "dim_supplier": {
        "_table": "Supplier (FMCG client) master. One row per supplier.",
        "supp_id": "Supplier identifier. Primary key.", "supp_nm": "Supplier name.",
        "tier_cd": "Supplier tier: K = key account, C = core, E = emerging.",
        "cat_typ": "Category type: FD = food, LQ = liquor, GM = general merchandise.",
    },
    "dim_merchandiser": {
        "_table": "Field merchandisers (reps) who visit stores. One row per rep.",
        "rep_id": "Merchandiser identifier. Primary key.", "rep_nm": "Merchandiser name.", "tl_nm": "Team lead name.",
        "rgn": "Region the merchandiser covers.", "strt_dt": "Date the merchandiser started.",
    },
    "fact_sales_weekly": {
        "_table": "Weekly sell-out (point-of-sale) sales. One row per store, SKU and week. Values in ZAR excl. VAT.",
        "wk_strt_dt": "Monday that starts the sales week. Joins to dim_date.dt.",
        "str_id": "Store identifier. Joins to dim_store.str_id.", "sku": "SKU identifier. Joins to dim_product.sku.",
        "qty": "Units sold.",
        "gsv": "Gross sales value in ZAR excl. VAT, before discounts. Also called gross sales or GSV.",
        "nsv": "Net sales value in ZAR excl. VAT, after promotional discounts and trade terms. Also called sales, net sales or NSV. The default meaning of 'sales'.",
        "cogs": "Cost of goods sold in ZAR.", "gp": "Gross profit (margin) in ZAR = nsv − cogs. Also called margin.",
        "prm_flg": "Promotion flag: Y = on promotion that week in that retailer group, N = regular price.",
        "prm_id": "Promotion identifier when prm_flg = Y. Joins to fact_promotions.prm_id.",
    },
    "fact_budget_monthly": {
        "_table": "Monthly net sales budget. One row per month, region, retailer group and category. ZAR excl. VAT.",
        "mth_strt_dt": "First day of the budget month.", "rgn": "Sales region. Matches dim_store.rgn.",
        "rtl_grp": "Retailer group. Matches dim_store.rtl_grp.", "cat": "Product category. Matches dim_product.cat.",
        "bgt_nsv": "Budgeted net sales value in ZAR excl. VAT. Compare with SUM(fact_sales_weekly.nsv).",
    },
    "fact_promotions": {
        "_table": "Promotions. One row per promotion, for one SKU in one retailer group.",
        "prm_id": "Promotion identifier. Primary key.", "prm_desc": "Promotion description.",
        "mech": "Promotion mechanic (10% Off, 20% Off, Buy 2 Get 1 Free, Multi-buy 2 for, Bundle Deal).",
        "prm_typ": "Promotion type: PR = price reduction, MB = multi-buy, BN = bundle.",
        "disc": "Effective discount percentage (0–100).", "sku": "SKU on promotion. Joins to dim_product.sku.",
        "rtl_grp": "Retailer group running the promotion.", "strt_dt": "First day of the promotion.", "end_dt": "Last day of the promotion.",
    },
    "fact_store_visits": {
        "_table": "Merchandiser store visits. One row per visit, with in-store execution measures.",
        "vst_id": "Visit identifier. Primary key.", "vst_dt": "Visit date.",
        "str_id": "Store visited. Joins to dim_store.str_id.", "rep_id": "Merchandiser. Joins to dim_merchandiser.rep_id.",
        "dur": "Visit duration in minutes.",
        "osa_pct": "On-shelf availability %: share of the expected SKUs found on shelf during the visit (0–100). Target 85%. Also called OSA, availability or in-stock rate.",
        "pog_comp": "Planogram compliance %: share of the shelf that matches the agreed planogram (0–100). Also called POG compliance.",
        "sos": "Share of shelf %: the supplier's share of shelf space in the category (0–100).",
    },
    "visit_notes": {
        "_table": "Free-text notes written by merchandisers during store visits. One row per note.",
        "nt_id": "Note identifier.", "vst_id": "Visit the note belongs to. Joins to fact_store_visits.vst_id.",
        "str_id": "Store. Joins to dim_store.str_id.", "rep_id": "Merchandiser. Joins to dim_merchandiser.rep_id.",
        "nt_dt": "Note date.", "nt_txt": "The merchandiser's comment in free text (for example 'shelf empty', 'display damaged').",
    },
}

cols_now = {}
for r in spark.sql(f"SELECT table_name, column_name FROM {isc}.columns WHERE table_schema = '{kit_schema}'").collect():
    cols_now.setdefault(r.table_name, set()).add(r.column_name)

for t, d in DESCRIPTIONS.items():
    if t not in cols_now:
        print(f"⚠️  kit.{t} not found, skipped"); continue
    for c, text in d.items():
        if c == "_table":
            spark.sql(f"COMMENT ON TABLE {q(catalog, kit_schema, t)} IS {lit(text)}")
        elif c in cols_now[t]:
            spark.sql(f"ALTER TABLE {q(catalog, kit_schema, t)} ALTER COLUMN `{c}` COMMENT {lit(text)}")
        else:
            print(f"⚠️  kit.{t}.{c} not found, skipped")
    print(f"✅ described kit.{t}")

display(spark.sql(f"""
    SELECT table_name, round(100 * count_if(comment IS NOT NULL AND trim(comment) <> '') / count(*), 0) AS pct_described
    FROM {isc}.columns WHERE table_schema = '{kit_schema}' GROUP BY 1 ORDER BY 1
"""))
# Tip: for the columns not covered here, use Catalog Explorer → kit table → AI generate → review → save.

# COMMAND ----------

# 6c · reference metric view (answer key for Sprint 2): readable names over the cryptic source columns.
MV_VERSION = "1.1"   # if your workspace rejects this, try "0.1"

def mv_sales_yaml(schema):
    return f"""
version: {MV_VERSION}
comment: "Weekly sell-out KPIs (reference)"
source: {catalog}.{schema}.fact_sales_weekly
joins:
  - name: store
    source: {catalog}.{schema}.dim_store
    on: source.str_id = store.str_id
  - name: product
    source: {catalog}.{schema}.dim_product
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
"""

try:
    spark.sql(f"CREATE OR REPLACE VIEW {q(catalog, kit_schema, 'mv_sales')} WITH METRICS LANGUAGE YAML AS $${mv_sales_yaml(kit_schema)}$$")
    display(spark.sql(f"""SELECT Region, MEASURE(Sales) AS sales, MEASURE(`Margin %`) AS margin_pct
                          FROM {q(catalog, kit_schema, 'mv_sales')} GROUP BY ALL ORDER BY sales DESC LIMIT 10"""))
except Exception as e:
    print(f"❌ mv_sales: {str(e)[:400]}\nFix the column names, or MV_VERSION, and re-run this cell.")

# Add mv_execution / mv_budget / mv_promo / mv_notes the same way once the data is final.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7 · Grants ⚠️ changes things
# MAGIC
# MAGIC Participants can **enter** the catalog and **create** their team schema, can **read** the source, and get **nothing** on the kit.
# MAGIC Skipped automatically while `participants_group` is blank (testing alone).
# MAGIC **Done when:** the grant listing shows `USE CATALOG, CREATE SCHEMA` on the catalog and `USE SCHEMA, SELECT` on the source.

# COMMAND ----------

if participants_group:
    g = f"`{participants_group}`"
    spark.sql(f"GRANT USE CATALOG, CREATE SCHEMA ON CATALOG {q(catalog)} TO {g}")
    spark.sql(f"GRANT USE SCHEMA, SELECT ON SCHEMA {SRC} TO {g}")
    display(spark.sql(f"SHOW GRANTS {g} ON CATALOG {q(catalog)}"))
    display(spark.sql(f"SHOW GRANTS {g} ON SCHEMA {SRC}"))
    print("Also give the group CAN USE on the hackathon SQL warehouse(s): SQL Warehouses → warehouse → Permissions.")
else:
    print("Skipped: participants_group is blank (testing alone).")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 8 · Test as an attendee, using the team notebook (manual, about 60–90 min)
# MAGIC
# MAGIC Test **exactly the way an attendee will**: open the attendee notebook yourself, and don't run it from here.
# MAGIC
# MAGIC 1. Open **`01_team_setup`** (in this folder), set `catalog` and `team_schema` (for example `team_01`), and click **Run all**.
# MAGIC    Check that every row count matches ✅, the constraints are present, and description coverage is low (expected).
# MAGIC 2. Follow `docs/attendee-guide.md` with one scenario (Scenario D, Client Executive, covers the most tables) in that team schema. Time each step.
# MAGIC
# MAGIC | Sprint | Test | Pass when |
# MAGIC |---|---|---|
# MAGIC | 0 · Team setup | Run `01_team_setup` as above | Row counts match, and the tables appear in Catalog Explorer with lineage to `hack_14oct` |
# MAGIC | 1 · Dashboard | Create a dashboard on the team tables, use the AI assistant for 3 visuals, add filters, publish | Published, and the AI assistant produces sensible charts |
# MAGIC | 2 · Metric views | Create `mv_sales` in the team schema from the attendee-guide template (Appendix A), and query it with `MEASURE()` | It returns rows, and the dashboard can use the metric view as a dataset |
# MAGIC | 3 · Genie baseline | Create a Genie space on the team tables, and ask the 10 Scenario D questions | You record a baseline. Expect several wrong answers (that's the point) |
# MAGIC | 4a · Descriptions | AI-generate the descriptions for 2 tables, then re-ask | The score goes up. If not, make the questions more ambiguous |
# MAGIC | 4a · Fallback | Run `02_apply_reference_descriptions` on the team schema | Descriptions applied, and Genie improves further |
# MAGIC | 4b · Tuning | Add instructions (fiscal year, sales = NSV), sample questions, and the metric view | Final score ≥ 8/10 |
# MAGIC | 5 · AI Functions | Run the Scenario E `ai_classify` example on 100 notes | Sensible issue types |
# MAGIC | 5 · App (optional) | Create an app, then use the 2 Genie Code prompts (attendee guide, Appendix C) | Tab 1 table and Tab 2 visuals work. Note the time it took |
# MAGIC
# MAGIC Write down the **expected answers** to every scenario's 10 questions while you test, and save them as `docs/genie-test-answers.md` (facilitator only).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 9 · Clean up after testing (manual)
# MAGIC
# MAGIC Drop the team schema you tested with, so the real team starts fresh. Run it yourself in the SQL editor, replacing the names:
# MAGIC
# MAGIC ```sql
# MAGIC DROP SCHEMA <catalog>.team_01 CASCADE;   -- the test team schema only, never hack_14oct or facilitator_kit
# MAGIC ```
# MAGIC
# MAGIC Delete any test dashboards, Genie spaces and apps by hand. *After the event:* drop each `team_XX` schema the same way, after agreeing
# MAGIC with the customer what to keep.
