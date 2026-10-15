# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Add attendees and check their access
# MAGIC
# MAGIC Use this **after** `00_facilitator_runbook` has set up `hack_14oct`, whenever you add attendees to `config.yaml`, or to repair an
# MAGIC attendee schema. Click **Run all**. It's safe to run any number of times: **nothing is ever deleted or recreated**.
# MAGIC
# MAGIC For **every attendee email in `config.yaml`**:
# MAGIC
# MAGIC | If their schema… | This notebook… |
# MAGIC |---|---|
# MAGIC | doesn't exist | creates it, copies every table from `hack_14oct`, adds the PK/FK constraints, and makes the attendee the owner |
# MAGIC | exists | leaves the data alone. It copies only **missing** tables, adds **missing** PK/FK constraints, and makes sure the attendee **owns** the schema and the hackathon tables |
# MAGIC
# MAGIC It also makes sure every attendee has `USE CATALOG`, read-only access to `hack_14oct`, and `CAN USE` on the SQL warehouse.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1 · Load the config file

# COMMAND ----------

import os, re

try:
    import yaml
except ImportError:
    raise ImportError("PyYAML isn't installed on this compute. Run `%pip install pyyaml` in a cell, then re-run this cell.")

nb_dir = os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())
CONFIG_PATH = os.path.join(nb_dir if nb_dir.startswith("/Workspace") else "/Workspace" + nb_dir, "config.yaml")
with open(CONFIG_PATH) as fh:
    cfg = yaml.safe_load(fh)

catalog = cfg["catalog"].strip()
warehouse_id = str(cfg["warehouse_id"]).strip()
source_schema = cfg.get("source_schema", "hack_14oct").strip()
attendees = sorted({str(e).strip().lower() for e in (cfg.get("attendees") or []) if "@" in str(e)})

def q(*parts):
    return ".".join(f"`{p}`" for p in parts)

def schema_for(email):
    """Schema name from the attendee's email: jane.doe@company.com -> jane_doe (the same rule as the runbook)."""
    return re.sub(r"[^0-9a-z]+", "_", email.split("@")[0].lower()).strip("_")

isc = f"{q(catalog)}.information_schema"
SRC = q(catalog, source_schema)

# The same keys as 00_facilitator_runbook, Step 4
PRIMARY_KEYS = {
    "dim_date": ["dt"], "dim_store": ["str_id"], "dim_product": ["sku"], "dim_supplier": ["supp_id"],
    "dim_merchandiser": ["rep_id"], "fact_promotions": ["prm_id"], "fact_store_visits": ["vst_id"],
}
FOREIGN_KEYS = [
    ("fact_sales_weekly", ["str_id"],     "dim_store",         ["str_id"]),
    ("fact_sales_weekly", ["sku"],        "dim_product",       ["sku"]),
    ("fact_sales_weekly", ["wk_strt_dt"], "dim_date",          ["dt"]),
    ("dim_product",       ["supp_id"],    "dim_supplier",      ["supp_id"]),
    ("fact_promotions",   ["sku"],        "dim_product",       ["sku"]),
    ("fact_store_visits", ["str_id"],     "dim_store",         ["str_id"]),
    ("fact_store_visits", ["rep_id"],     "dim_merchandiser",  ["rep_id"]),
    ("visit_notes",       ["vst_id"],     "fact_store_visits", ["vst_id"]),
]

src_tables = [r.table_name for r in spark.sql(f"""SELECT table_name FROM {isc}.tables
    WHERE table_schema = '{source_schema}' AND table_type IN ('MANAGED', 'EXTERNAL') ORDER BY 1""").collect()]
if not src_tables:
    raise ValueError(f"{SRC} has no tables. Run 00_facilitator_runbook first.")

print(f"Catalog   : {catalog}\nSource    : {SRC} ({len(src_tables)} tables)\nWarehouse : {warehouse_id}\nAttendees : {len(attendees)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2 · Attendee access (catalog, read-only source, warehouse)

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import WarehouseAccessControlRequest, WarehousePermissionLevel

w = WorkspaceClient()
access = {}
for email in attendees:
    try:
        spark.sql(f"GRANT USE CATALOG ON CATALOG {q(catalog)} TO `{email}`")
        spark.sql(f"GRANT USE SCHEMA, SELECT ON SCHEMA {SRC} TO `{email}`")
        access[email] = "✅"
    except Exception as e:
        access[email] = "❌ " + str(e).splitlines()[0][:150]

try:
    w.warehouses.update_permissions(warehouse_id, access_control_list=[
        WarehouseAccessControlRequest(user_name=e, permission_level=WarehousePermissionLevel.CAN_USE)
        for e, ok in access.items() if ok == "✅"])
    warehouse_ok = "✅"
except Exception as e:
    warehouse_ok = "❌ " + str(e).splitlines()[0][:150]
print(f"Warehouse CAN USE: {warehouse_ok}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3 · Create missing schemas, and check existing ones (tables, keys, owner)

# COMMAND ----------

def ensure_schema(email, schema):
    """Create the schema if it's missing; copy only missing tables; add missing keys; make the attendee the owner.
    Never drops or replaces data."""
    created = False
    if not spark.sql(f"SHOW SCHEMAS IN {q(catalog)} LIKE '{schema}'").count():
        spark.sql(f"CREATE SCHEMA {q(catalog, schema)} COMMENT 'Perfect Store hackathon: working schema of {email}, copied from {source_schema}'")
        created = True

    # Tables: copy only the ones that are missing
    have = {r.tableName for r in spark.sql(f"SHOW TABLES IN {q(catalog, schema)}").collect()}
    copied = [t for t in src_tables if t not in have]
    for t in copied:
        spark.sql(f"CREATE TABLE IF NOT EXISTS {q(catalog, schema, t)} DEEP CLONE {q(catalog, source_schema, t)}")

    # Keys: add missing primary keys; make sure every foreign key points at the attendee's own tables
    cons = spark.sql(f"""
        SELECT tc.table_name, tc.constraint_name, tc.constraint_type, rc.unique_constraint_schema AS ref_schema
        FROM {isc}.table_constraints tc
        LEFT JOIN {isc}.referential_constraints rc
          ON rc.constraint_schema = tc.constraint_schema AND rc.constraint_name = tc.constraint_name
        WHERE tc.constraint_schema = '{schema}'""").collect()
    has_pk = {r.table_name for r in cons if r.constraint_type == "PRIMARY KEY"}
    good_fk = {r.constraint_name for r in cons if r.constraint_type == "FOREIGN KEY" and r.ref_schema == schema}
    for r in cons:   # foreign keys that point somewhere else (for example at the source schema) are replaced
        if r.constraint_type == "FOREIGN KEY" and r.ref_schema != schema:
            spark.sql(f"ALTER TABLE {q(catalog, schema, r.table_name)} DROP CONSTRAINT IF EXISTS `{r.constraint_name}`")
    pk_added = 0
    for t, cols in PRIMARY_KEYS.items():
        if t not in has_pk:
            for c in cols:
                spark.sql(f"ALTER TABLE {q(catalog, schema, t)} ALTER COLUMN `{c}` SET NOT NULL")
            spark.sql(f"ALTER TABLE {q(catalog, schema, t)} ADD CONSTRAINT `pk_{t}` PRIMARY KEY ({', '.join(f'`{c}`' for c in cols)})")
            pk_added += 1
    fk_added = 0
    for child, ccols, parent, pcols in FOREIGN_KEYS:
        name = f"fk_{child}_{parent}"
        if name not in good_fk:
            spark.sql(f"""ALTER TABLE {q(catalog, schema, child)} ADD CONSTRAINT `{name}`
                          FOREIGN KEY ({', '.join(f'`{c}`' for c in ccols)}) REFERENCES {q(catalog, schema, parent)} ({', '.join(f'`{c}`' for c in pcols)})""")
            fk_added += 1

    # Owner: the attendee owns the schema and the hackathon tables (their own objects are left alone)
    owners = {r.table_name: r.table_owner for r in spark.sql(
        f"SELECT table_name, table_owner FROM {isc}.tables WHERE table_schema = '{schema}'").collect()}
    for t in src_tables:
        if (owners.get(t) or "").lower() != email:
            spark.sql(f"ALTER TABLE {q(catalog, schema, t)} OWNER TO `{email}`")
    schema_owner = spark.sql(f"SELECT schema_owner FROM {isc}.schemata WHERE schema_name = '{schema}'").first()[0]
    if (schema_owner or "").lower() != email:
        spark.sql(f"ALTER SCHEMA {q(catalog, schema)} OWNER TO `{email}`")

    status = "✅ created" if created else "✅ exists, checked"
    return status, len(copied), pk_added, fk_added

results, seen = [], {}
for email in attendees:
    schema = schema_for(email)
    seen[schema] = seen.get(schema, 0) + 1
    if seen[schema] > 1:
        schema = f"{schema}_{seen[schema]}"
    if schema == source_schema:
        results.append((email, schema, access[email], "❌ refused: same name as the source schema", 0, 0, 0)); continue
    try:
        status, copied, pk_added, fk_added = ensure_schema(email, schema)
        results.append((email, schema, access[email], status, copied, pk_added, fk_added))
    except Exception as e:
        results.append((email, schema, access[email], "❌ " + str(e).splitlines()[0][:200], 0, 0, 0))
    print(f"{results[-1][3][:2]} {email} → {schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4 · Report
# MAGIC
# MAGIC `tables_copied`, `pks_added` and `fks_added` count what this run **added**. 0 means everything was already in place.

# COMMAND ----------

display(spark.createDataFrame(results, "email string, schema string, access string, schema_status string, "
                                       "tables_copied long, pks_added long, fks_added long"))
print(f"Warehouse CAN USE: {warehouse_ok} · "
      f"{sum(r[3] == '✅ created' for r in results)} created, {sum(r[3] == '✅ exists, checked' for r in results)} checked, "
      f"{sum(r[3].startswith('❌') for r in results)} failed")
