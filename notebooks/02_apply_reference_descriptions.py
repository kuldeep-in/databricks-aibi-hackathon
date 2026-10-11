# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Apply the reference descriptions to a team schema (facilitator fallback)
# MAGIC
# MAGIC **Facilitator only.** Use this when a team runs out of time in **Sprint 4a: Describe your data**.
# MAGIC It copies the table and column descriptions from the answer-key schema (`facilitator_kit`) onto the matching tables
# MAGIC in a team schema.
# MAGIC
# MAGIC - `missing_only` (default): only fills in descriptions the team hasn't written yet, so the team's own work is kept.
# MAGIC - `overwrite`: replaces every description with the reference version.
# MAGIC
# MAGIC Re-score Genie afterwards, and note on the scoreboard that the reference descriptions were applied.

# COMMAND ----------

dbutils.widgets.text("catalog", "<your_catalog>", "1. Catalog")
dbutils.widgets.text("kit_schema", "<facilitator_kit_schema>", "2. Reference (answer-key) schema")
dbutils.widgets.text("team_schema", "team_XX", "3. Team schema")
dbutils.widgets.dropdown("mode", "missing_only", ["missing_only", "overwrite"], "4. Mode")

# COMMAND ----------

catalog = dbutils.widgets.get("catalog").strip()
kit_schema = dbutils.widgets.get("kit_schema").strip()
team_schema = dbutils.widgets.get("team_schema").strip()
mode = dbutils.widgets.get("mode")

def q(*parts):
    return ".".join(f"`{p}`" for p in parts)

def lit(text):
    return "'" + text.replace("\\", "\\\\").replace("'", "\\'") + "'"

def has_text(v):
    return v is not None and v.strip() != ""

isc = f"{q(catalog)}.information_schema"

# COMMAND ----------

team_tables = {r.table_name: r.comment for r in spark.sql(
    f"SELECT table_name, comment FROM {isc}.tables WHERE table_schema = '{team_schema}' AND table_type IN ('MANAGED','EXTERNAL')").collect()}
kit_tables = {r.table_name: r.comment for r in spark.sql(
    f"SELECT table_name, comment FROM {isc}.tables WHERE table_schema = '{kit_schema}' AND table_type IN ('MANAGED','EXTERNAL')").collect()}

team_cols = {(r.table_name, r.column_name): r.comment for r in spark.sql(
    f"SELECT table_name, column_name, comment FROM {isc}.columns WHERE table_schema = '{team_schema}'").collect()}
kit_cols = {(r.table_name, r.column_name): r.comment for r in spark.sql(
    f"SELECT table_name, column_name, comment FROM {isc}.columns WHERE table_schema = '{kit_schema}'").collect()}

applied, skipped = 0, 0

for t, ref in kit_tables.items():
    if t not in team_tables or not has_text(ref):
        continue
    if mode == "overwrite" or not has_text(team_tables[t]):
        spark.sql(f"COMMENT ON TABLE {q(catalog, team_schema, t)} IS {lit(ref)}")
        applied += 1
    else:
        skipped += 1

for (t, c), ref in kit_cols.items():
    if (t, c) not in team_cols or not has_text(ref):
        continue
    if mode == "overwrite" or not has_text(team_cols[(t, c)]):
        spark.sql(f"ALTER TABLE {q(catalog, team_schema, t)} ALTER COLUMN `{c}` COMMENT {lit(ref)}")
        applied += 1
    else:
        skipped += 1

print(f"✅ Applied {applied} descriptions to {team_schema} ({mode}); kept {skipped} existing team descriptions.")
