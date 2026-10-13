# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Attendee setup: create your own schema and copy the hackathon data into it
# MAGIC
# MAGIC **Perfect Store Command Centre: from sell-out to shelf**
# MAGIC
# MAGIC **Every attendee runs this once**, at the start (Sprint 0). It will:
# MAGIC 1. Create **your own schema** (by default named after you, for example `jane_doe`). You own it, so you can change anything in it.
# MAGIC 2. Copy every table from the read-only source schema `hack_14oct` with `DEEP CLONE` (an independent copy you can change freely).
# MAGIC 3. Re-apply the primary/foreign key constraints from the source tables (Genie uses them for joins).
# MAGIC 4. Validate the copy: row counts, constraints and description coverage.
# MAGIC
# MAGIC **How to run:** fill in the `catalog` widget at the top, then **Run all**. It takes about 1–2 minutes on serverless.
# MAGIC Broke your data later? Run it again to reset your copy. Metric views, dashboards and Genie spaces aren't affected.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration
# MAGIC Enter the **catalog** and **SQL warehouse ID** your facilitator gives you. Leave `my_schema` blank to use a schema named after you, or type your own name for it.

# COMMAND ----------

dbutils.widgets.text("catalog", "<your_catalog>", "1. Catalog")
dbutils.widgets.text("warehouse_id", "<warehouse_id>", "2. SQL warehouse ID")
dbutils.widgets.text("my_schema", "", "3. My schema (blank = named after me)")

# COMMAND ----------

catalog = dbutils.widgets.get("catalog").strip()
warehouse_id = dbutils.widgets.get("warehouse_id").strip()
source_schema = "hack_14oct"   # read-only source data
import re
me = spark.sql("SELECT current_user()").first()[0]
my_schema = dbutils.widgets.get("my_schema").strip() or re.sub(r"[^0-9a-z]+", "_", me.split("@")[0].lower()).strip("_")

def q(*parts):
    return ".".join(f"`{p}`" for p in parts)

src = q(catalog, source_schema)
dst = q(catalog, my_schema)
print(f"Source    : {src}  (read-only)\nMy schema : {dst}\nOwner     : {me}")

# Check that you can use the hackathon SQL warehouse (dashboards, Genie and your app run on it)
from databricks.sdk import WorkspaceClient
try:
    hw = WorkspaceClient().warehouses.get(warehouse_id)
    print(f"Warehouse : {hw.name} ({warehouse_id}) ✅")
except Exception as e:
    print(f"Warehouse : ⚠️ can't access '{warehouse_id}'. Check the ID, or ask your facilitator for CAN USE. ({str(e)[:120]})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Create your schema

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {dst} COMMENT 'Perfect Store hackathon: working schema of {me}, copied from {source_schema}'")
display(spark.sql(f"DESCRIBE SCHEMA EXTENDED {dst}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Copy every source table (DEEP CLONE)
# MAGIC Only tables are copied, not views or metric views. Building metric views is part of the hackathon.

# COMMAND ----------

tables = [r.table_name for r in spark.sql(f"""
    SELECT table_name FROM {q(catalog)}.information_schema.tables
    WHERE table_schema = '{source_schema}' AND table_type IN ('MANAGED', 'EXTERNAL')
    ORDER BY table_name
""").collect()]

if not tables:
    raise ValueError(f"No tables found in {src}. Ask your facilitator to check that the data is loaded.")

for t in tables:
    spark.sql(f"CREATE OR REPLACE TABLE {q(catalog, my_schema, t)} DEEP CLONE {q(catalog, source_schema, t)}")
    print(f"✅ cloned {t}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Re-apply PK/FK constraints
# MAGIC Primary keys first, then foreign keys (which reference your own copies of the tables).

# COMMAND ----------

isc = f"{q(catalog)}.information_schema"

key_cols = spark.sql(f"""
    SELECT tc.constraint_name, tc.constraint_type, tc.table_name,
           array_join(transform(array_sort(collect_list(struct(k.ordinal_position, k.column_name))), x -> concat('`', x.column_name, '`')), ', ') AS cols
    FROM {isc}.table_constraints tc
    JOIN {isc}.key_column_usage k
      ON k.constraint_schema = tc.constraint_schema AND k.constraint_name = tc.constraint_name
    WHERE tc.constraint_schema = '{source_schema}' AND tc.constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY')
    GROUP BY ALL
""").collect()

refs = {r.constraint_name: r.unique_constraint_name for r in spark.sql(f"""
    SELECT constraint_name, unique_constraint_name FROM {isc}.referential_constraints
    WHERE constraint_schema = '{source_schema}'
""").collect()}

pks = {r.constraint_name: r for r in key_cols if r.constraint_type == "PRIMARY KEY"}
fks = [r for r in key_cols if r.constraint_type == "FOREIGN KEY"]

def add_constraint(table, ddl, label):
    try:
        spark.sql(f"ALTER TABLE {q(catalog, my_schema, table)} ADD {ddl}")
        print(f"✅ {label}")
    except Exception as e:
        msg = str(e).split("\n")[0]
        status = "already present" if "already exists" in msg.lower() else f"skipped: {msg[:150]}"
        print(f"ℹ️  {label}: {status}")

for name, r in pks.items():
    add_constraint(r.table_name, f"CONSTRAINT `{name}` PRIMARY KEY ({r.cols})", f"PK {r.table_name}({r.cols})")

for r in fks:
    pk = pks.get(refs.get(r.constraint_name))
    if pk is None:
        print(f"⚠️  FK {r.constraint_name}: referenced key not found in the source schema, skipped")
        continue
    add_constraint(r.table_name,
                   f"CONSTRAINT `{r.constraint_name}` FOREIGN KEY ({r.cols}) REFERENCES {q(catalog, my_schema, pk.table_name)} ({pk.cols})",
                   f"FK {r.table_name}({r.cols}) → {pk.table_name}")

if not key_cols:
    print("ℹ️  The source schema has no PK/FK constraints to copy.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Validate

# COMMAND ----------

rows = []
for t in tables:
    s = spark.table(f"{q(catalog, source_schema, t)}").count()
    d = spark.table(f"{q(catalog, my_schema, t)}").count()
    rows.append((t, s, d, "✅" if s == d else "❌"))
display(spark.createDataFrame(rows, "table string, source_rows long, my_rows long, match string"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. What you've got, and what you'll need to add 💡
# MAGIC
# MAGIC Your tables are an exact copy of the source system. That means:
# MAGIC - **The column names are cryptic** (`str_id`, `sku`, `qty`, `nsv`, `gp`, `prm_flg`, `wk_strt_dt`, `rgn`, `fmt_cd`, `osa_pct`, `nt_txt` …).
# MAGIC - **Some values are codes** (`fmt_cd` = HYP / SUP / CNV / WHS, `sts` = O / C, `prm_typ` = PR / MB / BN, `prm_flg` = Y / N …).
# MAGIC - **There are no descriptions and no metric views.** You build those.
# MAGIC
# MAGIC The tables below show what you're starting from. Expect the dashboard AI assistant and Genie to **guess** (and often guess wrong)
# MAGIC until you add meaning to the data.

# COMMAND ----------

# Description coverage: 0% is expected. Raising it is your job in Sprint 4a (Describe your data).
display(spark.sql(f"""
    SELECT table_name,
           count(*) AS columns,
           count_if(comment IS NOT NULL AND trim(comment) <> '') AS described_columns,
           round(100 * count_if(comment IS NOT NULL AND trim(comment) <> '') / count(*), 0) AS pct_described,
           concat_ws(', ', collect_list(column_name)) AS columns_to_describe
    FROM {isc}.columns
    WHERE table_schema = '{my_schema}'
    GROUP BY table_name ORDER BY table_name
"""))

# COMMAND ----------

# Metric views in your schema: none yet. You create them in Sprint 2.
display(spark.sql(f"""
    SELECT count_if(table_type = 'METRIC_VIEW') AS metric_views, count_if(table_type IN ('MANAGED', 'EXTERNAL')) AS tables
    FROM {isc}.tables WHERE table_schema = '{my_schema}'
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ### 💡 Hints: how to get good results
# MAGIC
# MAGIC | If you see this… | …try this |
# MAGIC |---|---|
# MAGIC | The dashboard AI assistant picks the wrong column ("sales" → `gsv` instead of `nsv`) | **Add column descriptions** (Catalog Explorer → table → *AI generate* → review → save), or build the visual on a **metric view** measure |
# MAGIC | Every widget repeats the same SQL (`SUM(gp) / SUM(nsv)`) | **Create a metric view** with a `Margin %` measure once, and reuse it in every widget |
# MAGIC | Margin % looks wrong when you change the grouping | Define it as a **ratio measure in a metric view** (`SUM(gp) / SUM(nsv)`), not an average of percentages |
# MAGIC | Genie doesn't know what `nsv`, `osa_pct` or `fmt_cd = 'HYP'` mean | **Describe the columns and codes** in Unity Catalog, then add **synonyms** in the Genie space |
# MAGIC | Genie gets "last quarter" or "this year" wrong | Describe the fiscal columns in `dim_date` and add an **instruction**: the fiscal year runs March–February |
# MAGIC | Genie joins the wrong tables | Check the **PK/FK constraints** (already copied), describe the key columns, or add the **metric view** to the space |
# MAGIC | Genie's numbers differ from your dashboard | Point both at the **same metric view**, so they share one definition of each KPI |
# MAGIC
# MAGIC **Where to describe:** Catalog Explorer → your schema → table → *Overview* (table description) and *Columns* (column descriptions), using
# MAGIC **AI generate**, then **review and correct** it. Good descriptions say what the column means, its **unit and currency** (ZAR excl. VAT),
# MAGIC the table's **grain**, what the **codes** mean, and common **synonyms**.
# MAGIC
# MAGIC **Where to build metric views:** Catalog Explorer → your schema → *Create* → *Metric view* (or the SQL template in the attendee guide, Appendix A).
# MAGIC Give the measures and dimensions **business names** (`Sales`, `Margin %`, `Region`), so dashboards and Genie don't have to decode `nsv` or `rgn`.

# COMMAND ----------

# MAGIC %md
# MAGIC ✅ **Done.** Open **Catalog Explorer → your catalog → your schema**, look at the tables and their lineage, and continue with Sprint 1.
# MAGIC Use the **hackathon SQL warehouse** (the `warehouse_id` you entered) for your dashboard, your Genie space and your app.
# MAGIC Start with a quick dashboard as it is, then improve it with metric views (Sprint 2) and descriptions (Sprint 4a), and watch the results get better.
