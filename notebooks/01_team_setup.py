# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Team setup: copy the hackathon data into your team schema
# MAGIC
# MAGIC **Perfect Store Command Centre: from sell-out to shelf**
# MAGIC
# MAGIC Run this **once per team**, in Sprint 0. It will:
# MAGIC 1. Create your team schema (for example `team_03`) and, optionally, hand ownership to your team group.
# MAGIC 2. Copy every table from the source schema with `DEEP CLONE` (an independent copy you can change freely).
# MAGIC 3. Re-apply the primary/foreign key constraints from the source tables (Genie uses them for joins).
# MAGIC 4. Validate the copy: row counts, constraints and description coverage.
# MAGIC
# MAGIC **How to run:** fill in the widgets at the top, then **Run all**. It takes about 2–3 minutes on serverless.
# MAGIC Broke your data later? Run it again to reset your copy. Metric views, dashboards and Genie spaces aren't affected.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration
# MAGIC Replace the `<...>` placeholders. Your facilitator gives you the catalog name and your team number.

# COMMAND ----------

dbutils.widgets.text("catalog", "<your_catalog>", "1. Catalog")
dbutils.widgets.text("source_schema", "<source_schema>", "2. Source schema (read-only)")
dbutils.widgets.text("team_schema", "team_XX", "3. Team schema (team_01..team_05)")
dbutils.widgets.text("team_group", "", "4. Team group (optional owner)")

# COMMAND ----------

import re

catalog = dbutils.widgets.get("catalog").strip()
source_schema = dbutils.widgets.get("source_schema").strip()
team_schema = dbutils.widgets.get("team_schema").strip()
team_group = dbutils.widgets.get("team_group").strip()

def is_placeholder(v):
    return (not v) or v.startswith("<") or v == "team_XX"

missing = [n for n, v in [("catalog", catalog), ("source_schema", source_schema), ("team_schema", team_schema)] if is_placeholder(v)]
if missing:
    raise ValueError(f"Fill in the widget(s) {missing} before running. Replace the <...> placeholders.")
if not re.fullmatch(r"team_\d{2}", team_schema):
    raise ValueError(f"team_schema must look like 'team_03', got '{team_schema}'.")

def q(*parts):
    return ".".join(f"`{p}`" for p in parts)

src = q(catalog, source_schema)
dst = q(catalog, team_schema)
print(f"Source : {src}\nTarget : {dst}\nOwner  : {team_group or '(you)'}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Create the team schema

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {dst} COMMENT 'Perfect Store hackathon: team working schema, copied from {source_schema}'")
if team_group:
    spark.sql(f"ALTER SCHEMA {dst} OWNER TO `{team_group}`")
    print(f"Ownership of {dst} transferred to {team_group}")
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
    spark.sql(f"CREATE OR REPLACE TABLE {q(catalog, team_schema, t)} DEEP CLONE {q(catalog, source_schema, t)}")
    print(f"✅ cloned {t}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Re-apply PK/FK constraints
# MAGIC Primary keys first, then foreign keys (which reference the team's own copies of the tables).

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
        spark.sql(f"ALTER TABLE {q(catalog, team_schema, table)} ADD {ddl}")
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
                   f"CONSTRAINT `{r.constraint_name}` FOREIGN KEY ({r.cols}) REFERENCES {q(catalog, team_schema, pk.table_name)} ({pk.cols})",
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
    d = spark.table(f"{q(catalog, team_schema, t)}").count()
    rows.append((t, s, d, "✅" if s == d else "❌"))
display(spark.createDataFrame(rows, "table string, source_rows long, team_rows long, match string"))

# COMMAND ----------

# Description coverage. This is EXPECTED to be low at this point. You'll improve it in Sprint 4a (Describe your data).
display(spark.sql(f"""
    SELECT table_name,
           count(*) AS columns,
           count_if(comment IS NOT NULL AND trim(comment) <> '') AS described_columns,
           round(100 * count_if(comment IS NOT NULL AND trim(comment) <> '') / count(*), 0) AS pct_described
    FROM {isc}.columns
    WHERE table_schema = '{team_schema}'
    GROUP BY table_name ORDER BY table_name
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ✅ **Done.** Open **Catalog Explorer → your catalog → `team_XX`**, look at the tables and their lineage, and continue with Sprint 1.
