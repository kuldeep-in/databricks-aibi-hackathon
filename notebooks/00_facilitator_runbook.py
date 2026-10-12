# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Facilitator runbook: Perfect Store Command Centre hackathon
# MAGIC
# MAGIC **AI/BI Dashboards · Metric Views · Genie · Databricks Apps**
# MAGIC
# MAGIC This notebook walks you **step by step** through preparing and testing the hackathon environment. Run it **one section at a time**,
# MAGIC top to bottom. Don't use *Run all*. Each step says what it does, whether it changes anything, and what "done" looks like.
# MAGIC
# MAGIC | Step | What | Changes anything? |
# MAGIC |---|---|---|
# MAGIC | 0 | Configure (catalog widget, fixed settings) | No |
# MAGIC | 1 | Pre-flight checks (identity, catalog, warehouses, Apps) | No |
# MAGIC | 2 | Create the source schema `hack_14oct` | **Yes** |
# MAGIC | 3 | **Create the data:** generate the synthetic dataset as Delta tables in `hack_14oct`, then check it | **Yes** |
# MAGIC | 4 | Add PK/FK constraints to the source tables | **Yes** |
# MAGIC | 5 | Attendee permissions: the two grants to run yourself | Manual |
# MAGIC | 6 | **Test as an attendee:** open `01_attendee_setup` yourself (it creates your own schema and copies every table from `hack_14oct` into it), then test every sprint | Manual |
# MAGIC | 7 | Clean up the schema you tested with | Manual |
# MAGIC
# MAGIC **Related notebooks in this folder:**
# MAGIC - `01_attendee_setup`: run by **every attendee** in Sprint 0. It creates the attendee's own schema and copies every table (with constraints) from `hack_14oct` into it.
# MAGIC - `02_generate_synthetic_data`: the synthetic data generator, called from Step 3.
# MAGIC
# MAGIC **Docs in this folder:** `docs/hackathon-plan.md`, `docs/attendee-guide.md`

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 0 · Configuration
# MAGIC
# MAGIC **Widgets (fill in at the top of the notebook):**
# MAGIC
# MAGIC | Widget | Meaning |
# MAGIC |---|---|
# MAGIC | `catalog` | The one catalog for the whole hackathon. **Required** |
# MAGIC
# MAGIC **Fixed settings (variables in the next cell; edit there only if needed):**
# MAGIC
# MAGIC | Variable | Value | Meaning |
# MAGIC |---|---|---|
# MAGIC | `source_schema` | `hack_14oct` | The read-only source data schema that attendees copy from |

# COMMAND ----------

dbutils.widgets.text("catalog", "<your_catalog>", "1. Catalog")

# COMMAND ----------

catalog = dbutils.widgets.get("catalog").strip()

# Fixed settings
source_schema = "hack_14oct"          # read-only source data (make it read-only for participants)

def q(*parts):
    return ".".join(f"`{p}`" for p in parts)

isc = f"{q(catalog)}.information_schema"
SRC = q(catalog, source_schema)
print(f"Catalog : {catalog}\nSource  : {SRC}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 · Pre-flight checks (read-only)
# MAGIC
# MAGIC **Done when:** you're who you expect, the catalog exists, at least one serverless SQL warehouse is available, and the Apps API is reachable.

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
    print(f"✅ Databricks Apps API reachable: {len(apps)} app(s) in the workspace (check the quota: 1 app per attendee)")
except Exception as e:
    print(f"⚠️  Apps not available: {str(e)[:200]}")

# COMMAND ----------

# MAGIC %md
# MAGIC **Manual pre-flight checklist** (tick these off in the UI):
# MAGIC - [ ] **Genie** is enabled (sidebar → Genie → *New* is available)
# MAGIC - [ ] **AI/BI Dashboards** with the AI assistant work (sidebar → Dashboards → Create)
# MAGIC - [ ] **Metric views** can be created (Catalog Explorer → schema → *Create* → *Metric view*)
# MAGIC - [ ] **AI-generated descriptions** are available in Catalog Explorer (table → *AI generate*)
# MAGIC - [ ] **Genie Code** opens in the app/notebook editor
# MAGIC - [ ] **Custom Viz** (Public Preview) is available in dashboards (visualization → *Advanced → Custom Viz*), for the bonus custom visual
# MAGIC - [ ] A **SQL warehouse** exists for attendees (serverless, autoscaling 2–3 clusters), and you have its **ID** to share with them
# MAGIC - [ ] Partner-powered AI features are enabled in the workspace/account settings

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 · Create the source schema ⚠️ changes things
# MAGIC
# MAGIC Creates `hack_14oct`, where the data goes. Safe to re-run.
# MAGIC
# MAGIC > ⚠️ **Make the `hack_14oct` schema read-only for participants** (grant only `USE SCHEMA` and `SELECT`).
# MAGIC **Done when:** the schema appears in Catalog Explorer.

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SRC} COMMENT 'Perfect Store hackathon: read-only source data. Attendees copy from here.'")
display(spark.sql(f"SHOW SCHEMAS IN {q(catalog)}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 · Create the data as Delta tables in `hack_14oct` ⚠️ changes things
# MAGIC
# MAGIC **3a** runs `02_generate_synthetic_data`, which writes a fully synthetic, fictional dataset **straight into Delta tables** in the source
# MAGIC schema (10 tables, about 350K weekly sales rows over 156 weeks, insights planted, **no descriptions and no metric views**). It takes a few minutes on serverless.
# MAGIC Re-running it overwrites the tables with the same data (fixed seed). If you re-run it, re-run Step 4 too. **3b** checks the result.

# COMMAND ----------

# 3a · generate the synthetic dataset as Delta tables in the source schema
result = dbutils.notebook.run("./02_generate_synthetic_data", 3600, {"catalog": catalog})
print(result)
display(spark.sql(f"SHOW TABLES IN {SRC}"))

# COMMAND ----------

# MAGIC %md
# MAGIC **3b · Check the tables (read-only).** Confirms every table and the columns the attendee docs refer to exist.
# MAGIC **Done when:** every table is ✅.

# COMMAND ----------

# Columns the attendee docs, metric view starter and app prompts refer to
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
    print(f"ℹ️  Extra tables in the source (they'll also be copied by attendees): {extra}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 · PK/FK constraints on the source tables ⚠️ changes things
# MAGIC
# MAGIC Genie uses informational PK/FK constraints to join tables correctly, and `01_attendee_setup` copies them to every attendee schema.
# MAGIC PK columns must be `NOT NULL` (the cell sets this).
# MAGIC **Done when:** the constraint listing at the end shows your PKs and FKs.

# COMMAND ----------

PRIMARY_KEYS = {          # table -> [pk columns]   (matches 02_generate_synthetic_data)
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
# MAGIC ## Step 5 · Attendee permissions (manual)
# MAGIC
# MAGIC Every attendee must be able to **enter** the catalog, **create** their own schema, and **read** `hack_14oct`, and nothing more on it,
# MAGIC which keeps it read-only. Run these yourself in the SQL editor for the attendees (a group, or each user):
# MAGIC
# MAGIC ```sql
# MAGIC GRANT USE CATALOG, CREATE SCHEMA ON CATALOG <catalog> TO `<attendees>`;
# MAGIC GRANT USE SCHEMA, SELECT ON SCHEMA <catalog>.hack_14oct TO `<attendees>`;
# MAGIC ```
# MAGIC
# MAGIC Also give them **CAN USE** on the hackathon SQL warehouse: SQL Warehouses → warehouse → Permissions.
# MAGIC Share the **warehouse ID** with attendees, because `01_attendee_setup` asks for it.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6 · Test as an attendee, using the attendee notebook (manual, about 60–90 min)
# MAGIC
# MAGIC Test **exactly the way an attendee will**: open the attendee notebook yourself, and don't run it from here.
# MAGIC
# MAGIC 1. Open **`01_attendee_setup`** (in this folder), set `catalog` (leave `my_schema` blank to get a schema named after you), and click **Run all**.
# MAGIC    Check that every row count matches ✅, the constraints are present, and description coverage is low (expected).
# MAGIC 2. Follow `docs/attendee-guide.md` (what everyone builds, sprint by sprint) in that schema. Time each step.
# MAGIC
# MAGIC | Sprint | Test | Pass when |
# MAGIC |---|---|---|
# MAGIC | 0 · Attendee setup | Run `01_attendee_setup` as above | Row counts match, and the tables appear in Catalog Explorer with lineage to `hack_14oct` |
# MAGIC | 1 · Dashboard | Create a dashboard on your tables, use the AI assistant for 3 visuals, add filters, publish | Published, and the AI assistant produces sensible charts |
# MAGIC | 2 · Metric views | Create `mv_sales` in your schema from the attendee-guide template (Appendix A), and query it with `MEASURE()` | It returns rows, and the dashboard can use the metric view as a dataset |
# MAGIC | 3 · Genie quick win | Create a Genie space on your tables, and ask the 10 questions from the attendee guide | Expect several wrong or unclear answers (that's the point) |
# MAGIC | 4a · Descriptions | AI-generate the descriptions for 2 tables, then re-ask | The answers get better |
# MAGIC | 4b · Tuning | Add instructions (fiscal year, sales = NSV), sample questions, and the metric view | Most questions are now answered well |
# MAGIC | 5 · App | Create an app, then use the 2 Genie Code prompts (attendee guide, Appendix C) | Tab 1 table and Tab 2 visuals work. Note the time it took |
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7 · Clean up after testing (manual)
# MAGIC
# MAGIC Drop the schema you tested with. Run it yourself in the SQL editor, replacing the names:
# MAGIC
# MAGIC ```sql
# MAGIC DROP SCHEMA <catalog>.<your_test_schema> CASCADE;   -- your test schema only, never hack_14oct
# MAGIC ```
# MAGIC
# MAGIC Delete any test dashboards, Genie spaces and apps by hand. *After the event:* drop each attendee schema the same way, after agreeing
# MAGIC with the customer what to keep.
