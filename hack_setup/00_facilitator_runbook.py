# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Hackathon setup: Perfect Store Command Centre
# MAGIC
# MAGIC **AI/BI Dashboards · Metric Views · Genie · Databricks Apps**
# MAGIC
# MAGIC **One execution sets up everything:** the read-only source schema `hack_14oct` with the synthetic data, and one schema per
# MAGIC attendee with their own copy of the data. Fill in the config file, then click **Run all** (about 10–20 minutes).
# MAGIC
# MAGIC Everything is driven by **one config file**, `hack_setup/config.yaml`: the catalog, the SQL warehouse ID, the source schema and the
# MAGIC attendee list (name and email). There are no widgets. It's safe to run again, for example after adding attendees:
# MAGIC existing attendee schemas are never touched.
# MAGIC
# MAGIC | Step | What | Changes anything? |
# MAGIC |---|---|---|
# MAGIC | 0 | Load the config file | No |
# MAGIC | 1 | Pre-flight checks (identity, catalog, warehouse, Apps) | No |
# MAGIC | 2 | Create the source schema `hack_14oct` | **Yes** |
# MAGIC | 3 | **Create the data:** generate the synthetic dataset as Delta tables in `hack_14oct`, then check it | **Yes** |
# MAGIC | 4 | Add PK/FK constraints to the source tables | **Yes** |
# MAGIC | 5 | Attendee access: `USE CATALOG`, read-only access to `hack_14oct`, and `CAN USE` on the warehouse, for every attendee in the config | **Yes** |
# MAGIC | 6 | **Create attendee schemas:** one per attendee, with a copy of every table, owned by the attendee | **Yes** |
# MAGIC | 7 | Summary: source tables and attendee schemas | No |
# MAGIC
# MAGIC After the run: **test as an attendee** and **clean up** (manual, see the end of this notebook).
# MAGIC
# MAGIC **Files in this folder:** `config.yaml` (settings), `01_generate_synthetic_data` (called from Step 3).
# MAGIC
# MAGIC **Docs:** `docs/hackathon-plan.md` (facilitator plan), `attendees/01_instructions.md` (attendee instructions)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 0 · Load the config file
# MAGIC
# MAGIC 1. Open **`config.yaml`** in this `hack_setup/` folder.
# MAGIC 2. Set `catalog`, `warehouse_id` and the `attendees` list (**one email per attendee**). Add **yourself** too, so you get a test schema.
# MAGIC 3. Click **Run all**.
# MAGIC
# MAGIC ⚠️ The repo is public: edit `config.yaml` in your workspace copy only, and **don't commit real emails or IDs**.
# MAGIC **Done when:** the cell prints your settings and the number of attendees.

# COMMAND ----------

import os, re

try:
    import yaml
except ImportError:
    raise ImportError("PyYAML isn't installed on this compute. Run `%pip install pyyaml` in a cell, then re-run this cell.")

nb_dir = os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())
CONFIG_PATH = os.path.join(nb_dir if nb_dir.startswith("/Workspace") else "/Workspace" + nb_dir, "config.yaml")
if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"{CONFIG_PATH} not found. It should be in the same folder as this notebook.")

with open(CONFIG_PATH) as fh:
    cfg = yaml.safe_load(fh)

catalog = cfg["catalog"].strip()
warehouse_id = str(cfg["warehouse_id"]).strip()
source_schema = cfg.get("source_schema", "hack_14oct").strip()
def schema_for(email):
    """Schema name from the attendee's email: jane.doe@company.com -> jane_doe."""
    return re.sub(r"[^0-9a-z]+", "_", email.split("@")[0].lower()).strip("_")

attendees = sorted({str(e).strip().lower() for e in (cfg.get("attendees") or []) if "@" in str(e)})

def q(*parts):
    return ".".join(f"`{p}`" for p in parts)

isc = f"{q(catalog)}.information_schema"
SRC = q(catalog, source_schema)
print(f"Config    : {CONFIG_PATH}\nCatalog   : {catalog}\nWarehouse : {warehouse_id}\nSource    : {SRC}\nAttendees : {len(attendees)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 · Pre-flight checks (read-only)
# MAGIC
# MAGIC **Done when:** you're who you expect, the catalog and the warehouse from `config.yaml` exist, and the Apps API is reachable.

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
    hw = w.warehouses.get(warehouse_id)
    print(f"✅ Hackathon warehouse: {hw.name} ({warehouse_id}) · {hw.state} · size {hw.cluster_size} · "
          f"serverless {bool(hw.enable_serverless_compute)} · clusters {hw.min_num_clusters}–{hw.max_num_clusters}")
    if (hw.max_num_clusters or 1) < 2:
        print("ℹ️  For 20 attendees, consider autoscaling to at least 2–3 clusters.")
except Exception as e:
    print(f"❌ Warehouse '{warehouse_id}' from config.yaml not found or not accessible: {str(e)[:200]}")


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
# MAGIC - [ ] Partner-powered AI features are enabled in the workspace/account settings

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 · Create the source schema ⚠️ changes things
# MAGIC
# MAGIC Creates `hack_14oct`, where the data goes. Safe to re-run.
# MAGIC
# MAGIC > ⚠️ `hack_14oct` must stay **read-only** for attendees. Step 5 grants them only `USE SCHEMA` and `SELECT` on it.
# MAGIC **Done when:** the schema appears in Catalog Explorer.

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SRC} COMMENT 'Perfect Store hackathon: read-only source data. Attendees copy from here.'")
display(spark.sql(f"SHOW SCHEMAS IN {q(catalog)}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 · Create the data as Delta tables in `hack_14oct` ⚠️ changes things
# MAGIC
# MAGIC **3a** runs `01_generate_synthetic_data`, which writes a fully synthetic, fictional dataset **straight into Delta tables** in the source
# MAGIC schema (10 tables, about 350K weekly sales rows over 156 weeks, insights planted, **no descriptions and no metric views**). It takes a few minutes on serverless.
# MAGIC Re-running it overwrites the source tables with the same data (fixed seed). Step 4 then re-adds the constraints.

# COMMAND ----------

# 3a · generate the synthetic dataset as Delta tables in the source schema
result = dbutils.notebook.run("./01_generate_synthetic_data", 3600)   # reads config.yaml itself
print(result)
display(spark.sql(f"SHOW TABLES IN {SRC}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 · PK/FK constraints on the source tables ⚠️ changes things
# MAGIC
# MAGIC Genie uses informational PK/FK constraints to join tables correctly, and Step 6 copies them to every attendee schema.
# MAGIC PK columns must be `NOT NULL` (the cell sets this).
# MAGIC **Done when:** the constraint listing at the end shows your PKs and FKs.

# COMMAND ----------

PRIMARY_KEYS = {          # table -> [pk columns]   (matches 01_generate_synthetic_data)
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
# MAGIC ## Step 5 · Attendee access ⚠️ changes things
# MAGIC
# MAGIC For **every attendee in `config.yaml`**, this grants to their **email**:
# MAGIC - `USE CATALOG` on the catalog
# MAGIC - `USE SCHEMA` + `SELECT` on `hack_14oct` (read-only, so they can also reset their own copy later)
# MAGIC - `CAN USE` on the hackathon SQL warehouse
# MAGIC
# MAGIC Attendees **don't get `CREATE SCHEMA`**: you create their schemas in Step 6. Safe to re-run, for example after adding attendees.
# MAGIC **Done when:** every attendee shows ✅.

# COMMAND ----------

from databricks.sdk.service.sql import WarehouseAccessControlRequest, WarehousePermissionLevel

access = []
for email in attendees:
    try:
        spark.sql(f"GRANT USE CATALOG ON CATALOG {q(catalog)} TO `{email}`")
        spark.sql(f"GRANT USE SCHEMA, SELECT ON SCHEMA {SRC} TO `{email}`")
        access.append((email, "✅", ""))
    except Exception as e:
        access.append((email, "❌", str(e).splitlines()[0][:200]))

try:
    w.warehouses.update_permissions(warehouse_id, access_control_list=[
        WarehouseAccessControlRequest(user_name=e, permission_level=WarehousePermissionLevel.CAN_USE)
        for e, ok, _ in access if ok == "✅"])
    print(f"✅ CAN USE on warehouse {warehouse_id} granted to {sum(ok == '✅' for _, ok, _ in access)} attendee(s)")
except Exception as e:
    print(f"❌ Warehouse permissions: {str(e)[:300]}")

display(spark.createDataFrame(access, "email string, catalog_and_source_grants string, error string"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6 · Create attendee schemas ⚠️ changes things
# MAGIC
# MAGIC For **every attendee in `config.yaml`**, this:
# MAGIC 1. creates their schema, named after their **email** (`jane.doe@company.com` → `jane_doe`),
# MAGIC 2. deep clones every table from `hack_14oct` into it, and adds the PK/FK constraints from Step 4,
# MAGIC 3. makes the attendee the **owner** of the schema and of every table in it (so they can describe and change everything).
# MAGIC
# MAGIC If an attendee's schema **already exists**, it isn't created or copied: the report only shows how many tables it has.
# MAGIC The first cell shows the plan. The second cell does the work (about 20–40 seconds per new attendee).

# COMMAND ----------

# 6a · preview (changes nothing)
existing = {r[0] for r in spark.sql(f"SHOW SCHEMAS IN {q(catalog)}").collect()}
plan, seen = [], {}
for email in attendees:
    name = schema_for(email)
    seen[name] = seen.get(name, 0) + 1
    if seen[name] > 1:
        name = f"{name}_{seen[name]}"
    plan.append((email, name, f"exists: {spark.sql(f'SHOW TABLES IN {q(catalog, name)}').count()} tables" if name in existing else "new"))
display(spark.createDataFrame(plan, "email string, schema string, status string"))
# Two emails with the same name part (jane.doe@a.com, jane.doe@b.com) get jane_doe and jane_doe_2: tell the second one which schema is theirs.

# COMMAND ----------

# 6b · create the schemas, copy the tables, set the owners
src_tables = [r.table_name for r in spark.sql(f"""SELECT table_name FROM {isc}.tables
    WHERE table_schema = '{source_schema}' AND table_type IN ('MANAGED', 'EXTERNAL') ORDER BY 1""").collect()]

def quiet(sql):
    try:
        spark.sql(sql)
    except Exception as e:
        if "already exists" not in str(e).lower():
            raise

results = []
for email, name, status in plan:
    if name in (source_schema,):
        results.append((email, name, 0, "❌ refused: same name as the source schema")); continue
    if status != "new":
        results.append((email, name, spark.sql(f"SHOW TABLES IN {q(catalog, name)}").count(), "exists")); continue
    try:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {q(catalog, name)} COMMENT 'Perfect Store hackathon: working schema of {email}, copied from {source_schema}'")
        for t in src_tables:
            spark.sql(f"CREATE OR REPLACE TABLE {q(catalog, name, t)} DEEP CLONE {q(catalog, source_schema, t)}")
        for t, cols in PRIMARY_KEYS.items():
            quiet(f"ALTER TABLE {q(catalog, name, t)} ADD CONSTRAINT `pk_{t}` PRIMARY KEY ({', '.join(f'`{c}`' for c in cols)})")
        for child, ccols, parent, pcols in FOREIGN_KEYS:
            quiet(f"""ALTER TABLE {q(catalog, name, child)} ADD CONSTRAINT `fk_{child}_{parent}`
                      FOREIGN KEY ({', '.join(f'`{c}`' for c in ccols)}) REFERENCES {q(catalog, name, parent)} ({', '.join(f'`{c}`' for c in pcols)})""")
        for t in src_tables:
            spark.sql(f"ALTER TABLE {q(catalog, name, t)} OWNER TO `{email}`")
        spark.sql(f"ALTER SCHEMA {q(catalog, name)} OWNER TO `{email}`")
        results.append((email, name, len(src_tables), "✅ created, owner set"))
    except Exception as e:
        results.append((email, name, 0, "❌ " + str(e).splitlines()[0][:200]))
    print(f"{results[-1][3][:2]} {email} → {name}")

display(spark.createDataFrame(results, "email string, schema string, tables long, status string"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7 · Summary
# MAGIC
# MAGIC **Done when:** every source table has rows, and every attendee shows ✅ or `exists`.

# COMMAND ----------

display(spark.createDataFrame([(t, spark.table(q(catalog, source_schema, t)).count()) for t in src_tables],
                              "source_table string, rows long"))
display(spark.createDataFrame(results, "email string, schema string, tables long, status string"))
print(f"✅ Setup finished: {len(src_tables)} source tables in {SRC}, "
      f"{sum(r[3].startswith('✅') for r in results)} schema(s) created, {sum(r[3] == 'exists' for r in results)} already existed, "
      f"{sum(r[3].startswith('❌') for r in results)} failed.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## After the run: test as an attendee (manual, about 60–90 min)
# MAGIC
# MAGIC Add **yourself** to `config.yaml` before the run, so you get a schema too. Then test **exactly the way an attendee will**:
# MAGIC follow `attendees/01_instructions.md` in your schema, and time each step.
# MAGIC
# MAGIC | Sprint | Test | Pass when |
# MAGIC |---|---|---|
# MAGIC | 0 · Setup | Open your schema in Catalog Explorer | 10 tables, lineage to `hack_14oct`, you're the owner, no descriptions |
# MAGIC | 1 · Dashboard | Create a dashboard on your tables, use the AI assistant for 3 visuals, add filters, publish | Published, and the AI assistant produces sensible charts |
# MAGIC | 2 · Metric views | Create `mv_sales` in your schema from the starter (instructions, Appendix A), and query it with `MEASURE()` | It returns rows, and the dashboard can use the metric view as a dataset |
# MAGIC | 2 · Bonus | Build the Custom Viz bullet chart (instructions, Appendix D) | The chart renders |
# MAGIC | 3 · Genie quick win | Create a Genie space on your tables, and ask the 10 questions from the instructions | Expect several wrong or unclear answers (that's the point) |
# MAGIC | 4a · Descriptions | AI-generate the descriptions for 2 tables, then re-ask | The answers get better |
# MAGIC | 4b · Tuning | Add instructions (fiscal year, sales = NSV), sample questions, and the metric view | Most questions are now answered well |
# MAGIC | 5 · App | Create an app, then use the 2 Genie Code prompts (instructions, Appendix C) | Tab 1 table and Tab 2 visuals work. Note the time it took |

# COMMAND ----------

# MAGIC %md
# MAGIC ## After testing: clean up (manual)
# MAGIC
# MAGIC Drop your test schema, then run this notebook again to get a fresh copy. Run this yourself in the SQL editor:
# MAGIC
# MAGIC ```sql
# MAGIC DROP SCHEMA <catalog>.<your_test_schema> CASCADE;   -- your test schema only, never hack_14oct
# MAGIC ```
# MAGIC
# MAGIC The same applies if an attendee breaks their data: drop their schema and run this notebook again.
# MAGIC Delete any test dashboards, Genie spaces and apps by hand. *After the event:* drop each attendee schema the same way, after agreeing
# MAGIC with the customer what to keep.
