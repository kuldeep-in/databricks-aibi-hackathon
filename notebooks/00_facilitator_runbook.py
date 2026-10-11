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
# MAGIC | 0 | Configure the placeholders (catalog, schemas, groups) | No |
# MAGIC | 1 | Pre-flight checks (identity, catalog, warehouses, AI Functions, Apps) | No |
# MAGIC | 2 | Create the source and facilitator-kit schemas | **Yes** |
# MAGIC | 3 | **Load the data:** generate the synthetic dataset (default), or download or upload files and load them, then check the data contract | **Yes** |
# MAGIC | 4 | Check the description strategy (the source should be almost undocumented) | Optional |
# MAGIC | 5 | Add PK/FK constraints to the source tables | **Yes** |
# MAGIC | 6 | Build the facilitator kit: clone, reference descriptions, reference metric views | **Yes** |
# MAGIC | 7 | Grant permissions to participants | **Yes** |
# MAGIC | 8 | Dry run as a test team: `01_team_setup` **copies every object from the source schema into a team schema** | **Yes** |
# MAGIC | 9 | Test every sprint (dashboard, metric view, descriptions, Genie, app) | Manual |
# MAGIC | 10 | Cleanup of the test team (guarded) | **Yes (destructive)** |
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
# MAGIC Fill in the widgets at the top of the notebook. **Every `<...>` value must be replaced**, or the following cells stop with an error.
# MAGIC
# MAGIC | Widget | Meaning | Suggested value |
# MAGIC |---|---|---|
# MAGIC | `catalog` | The one catalog for the whole hackathon | *your choice* |
# MAGIC | `source_schema` | The read-only source data schema that teams copy from | for example `hack` |
# MAGIC | `kit_schema` | The facilitator-only answer key (described tables, reference metric views) | for example `facilitator_kit` |
# MAGIC | `participants_group` | The account group that contains all attendees (leave blank while testing alone) | for example `hackathon_participants` |
# MAGIC | `test_team_schema` | The team schema used for your dry run | `team_99` |
# MAGIC | `test_team_group` | An optional group to own the test team schema (blank = you) | blank |
# MAGIC | `github_repo` / `github_branch` / `github_data_path` | The public GitHub repo, branch and folder that the data files are downloaded from (Step 3b) | `kuldeep-in/databricks-aibi-hackathon` / `main` / `data` |

# COMMAND ----------

dbutils.widgets.text("catalog", "<your_catalog>", "1. Catalog")
dbutils.widgets.text("source_schema", "<source_schema>", "2. Source schema")
dbutils.widgets.text("kit_schema", "<facilitator_kit_schema>", "3. Facilitator kit schema")
dbutils.widgets.text("participants_group", "", "4. Participants group (optional)")
dbutils.widgets.text("test_team_schema", "team_99", "5. Test team schema")
dbutils.widgets.text("test_team_group", "", "6. Test team group (optional)")
dbutils.widgets.text("confirm_cleanup", "", "7. Cleanup confirmation (Step 10)")
dbutils.widgets.text("github_repo", "kuldeep-in/databricks-aibi-hackathon", "8. GitHub repo (owner/name) for data files")
dbutils.widgets.text("github_branch", "main", "9. GitHub branch")
dbutils.widgets.text("github_data_path", "data", "10. Data folder in the repo")

# COMMAND ----------

catalog = dbutils.widgets.get("catalog").strip()
source_schema = dbutils.widgets.get("source_schema").strip()
kit_schema = dbutils.widgets.get("kit_schema").strip()
participants_group = dbutils.widgets.get("participants_group").strip()
test_team_schema = dbutils.widgets.get("test_team_schema").strip()
test_team_group = dbutils.widgets.get("test_team_group").strip()

bad = [n for n, v in [("catalog", catalog), ("source_schema", source_schema), ("kit_schema", kit_schema),
                      ("test_team_schema", test_team_schema)] if not v or v.startswith("<")]
if bad:
    raise ValueError(f"Step 0: replace the placeholder widget(s) {bad} before continuing.")

def q(*parts):
    return ".".join(f"`{p}`" for p in parts)

def lit(text):
    return "'" + text.replace("\\", "\\\\").replace("'", "\\'") + "'"

isc = f"{q(catalog)}.information_schema"
SRC, KIT, TEST = q(catalog, source_schema), q(catalog, kit_schema), q(catalog, test_team_schema)
print(f"Catalog      : {catalog}\nSource       : {SRC}\nKit          : {KIT}\nTest team    : {TEST}\nParticipants : {participants_group or '(not set: testing alone)'}")

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
# MAGIC **Done when:** both schemas appear in Catalog Explorer.

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SRC} COMMENT 'Perfect Store hackathon: read-only source data. Teams copy from here.'")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {KIT} COMMENT 'Perfect Store hackathon: FACILITATOR ONLY answer key. Not granted to participants.'")
display(spark.sql(f"SHOW SCHEMAS IN {q(catalog)}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 · Load the data into the source schema ⚠️ changes things
# MAGIC
# MAGIC The hackathon data goes into the source schema as Delta tables. There are three ways to get it there:
# MAGIC - **Option A (default): generate it.** `03_generate_synthetic_data` writes a fully synthetic, fictional dataset straight into the
# MAGIC   source schema, with the insights already planted. Run cell **3-A**, then skip to **3e**.
# MAGIC - **Option B: download files** from the `data/` folder of a public GitHub repo (cell 3b), then load them with 3c–3d.
# MAGIC - **Option C: upload your own files** to the Volume by hand, then load them with 3c–3d.
# MAGIC
# MAGIC **Ground rules for your files:** **fictional** retailers, suppliers and brands only, ZAR, South African regions, a March–February
# MAGIC fiscal year, and business abbreviations kept in the column names (`nsv`, `osa_pct`, `pog_comp`, `fy_wk`, `rtl_grp`). Plant the
# MAGIC insights from `docs/hackathon-plan.md` §3.1 (the OSA < 85% region, a loss-making promo mechanic, seasonality, and so on).
# MAGIC Convert any Excel files to CSV or Parquet first.
# MAGIC
# MAGIC | Sub-step | What | Changes anything? |
# MAGIC |---|---|---|
# MAGIC | **3-A** | **Option A:** run the synthetic data generator (about 5–10 min on serverless) | **Yes** |
# MAGIC | 3a | Create the landing Volume `<source_schema>.landing` | **Yes** |
# MAGIC | 3a–3d | *Options B and C only:* create the landing Volume, get the files into it (**B:** download from GitHub, **C:** upload by hand in Catalog Explorer), preview them, and load them | **Yes** |
# MAGIC | 3c | List the files and preview how they map to table names | No |
# MAGIC | 3d | Load every file into a Delta table (overwrite) | **Yes** |
# MAGIC | 3e | Check the data contract | No |
# MAGIC
# MAGIC **File naming = table naming:** `fact_sales_weekly.csv` → table `fact_sales_weekly`. A **folder** of files also works
# MAGIC (`fact_sales_weekly/part-0001.parquet`, …), which is handy for big facts. Column names are cleaned to `lower_snake_case`.
# MAGIC
# MAGIC *Already loaded the tables another way?* Skip 3a–3d and go straight to **3e**.

# COMMAND ----------

# 3-A · Option A (default): generate the synthetic dataset into the source schema (overwrites the generated tables)
# Sizes can be changed in the generator's widgets. The defaults give about 3.5M weekly sales rows over 156 weeks.
result = dbutils.notebook.run("./03_generate_synthetic_data", 3600, {"catalog": catalog, "schema": source_schema})
print(result)

# COMMAND ----------

# 3a · landing Volume for the source files
spark.sql(f"CREATE VOLUME IF NOT EXISTS {q(catalog, source_schema, 'landing')} COMMENT 'Hackathon source files (CSV/Parquet/JSON), loaded into the source schema by Step 3d'")
LANDING = f"/Volumes/{catalog}/{source_schema}/landing"
print(f"✅ Upload your files to: {LANDING}\n   (Catalog Explorer → {catalog} → {source_schema} → Volumes → landing → Upload to this volume)")

# COMMAND ----------

# 3b · Option B: download the data files from the public GitHub repo into the landing Volume
# (Option C: skip this cell and upload the files by hand in Catalog Explorer.)
# Needs outbound internet access from the compute to api.github.com and raw.githubusercontent.com.
import os, requests

GH_REPO = dbutils.widgets.get("github_repo").strip()
GH_BRANCH = dbutils.widgets.get("github_branch").strip()
GH_PATH = dbutils.widgets.get("github_data_path").strip().strip("/")
DATA_EXT = (".csv", ".parquet", ".json")

def gh_list(path):
    """Recursively list the data files under `path` in the repo, as (relative_path, download_url, size)."""
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", params={"ref": GH_BRANCH}, timeout=30)
    r.raise_for_status()
    out = []
    for item in r.json():
        if item["type"] == "dir":
            out += gh_list(item["path"])
        elif item["name"].lower().endswith(DATA_EXT):
            out.append((item["path"][len(GH_PATH) + 1:], item["download_url"], item["size"]))
    return out

files = gh_list(GH_PATH)
if not files:
    raise ValueError(f"No CSV/Parquet/JSON files found in github.com/{GH_REPO}/tree/{GH_BRANCH}/{GH_PATH}")

for rel, url, size in files:
    target = f"{LANDING}/{rel}"
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with requests.get(url, stream=True, timeout=300) as resp:
        resp.raise_for_status()
        with open(target, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=8 * 1024 * 1024):
                fh.write(chunk)
    print(f"✅ {rel} ({size / 1_048_576:.1f} MB) → {target}")

print(f"\nDownloaded {len(files)} file(s) from github.com/{GH_REPO} ({GH_BRANCH}/{GH_PATH})")

# COMMAND ----------

# 3c · list the files and preview the file → table mapping (read-only)
import re

FORMATS = {".csv": "csv", ".parquet": "parquet", ".json": "json"}

def clean_name(name):
    return re.sub(r"_+", "_", re.sub(r"[^0-9a-zA-Z]+", "_", name.strip())).strip("_").lower()

def detect(entry):
    """Return (table_name, format, path) for a file or a folder in the landing Volume, or None if unsupported."""
    name = entry.name.rstrip("/")
    if entry.isDir():
        files = [f for f in dbutils.fs.ls(entry.path) if not f.name.startswith(("_", "."))]
        exts = {("." + f.name.rsplit(".", 1)[-1].lower()) for f in files if "." in f.name}
        fmt = next((FORMATS[e] for e in exts if e in FORMATS), None)
        return (clean_name(name), fmt, entry.path) if fmt else None
    stem, _, ext = name.rpartition(".")
    fmt = FORMATS.get("." + ext.lower())
    return (clean_name(stem), fmt, entry.path) if fmt else None

entries = [e for e in dbutils.fs.ls(LANDING) if not e.name.startswith(("_", "."))]
plan = [d for d in (detect(e) for e in entries) if d]
skipped = [e.name for e in entries if not detect(e)]

if not plan:
    print(f"⚠️  No CSV/Parquet/JSON files found in {LANDING}. Upload your files first (3b).")
else:
    display(spark.createDataFrame(plan, "table string, format string, path string"))
if skipped:
    print(f"ℹ️  Skipped (unsupported format): {skipped}")

# COMMAND ----------

# 3d · load every file/folder into a Delta table in the source schema (overwrites existing tables of the same name)
ONLY_TABLES = []   # optional: restrict to these tables, for example ["fact_sales_weekly"]; empty = load all

def read_source(fmt, path):
    reader = spark.read.format(fmt)
    if fmt == "csv":
        reader = reader.option("header", True).option("inferSchema", True).option("multiLine", True).option("escape", '"')
    return reader.load(path)

loaded_summary = []
for table, fmt, path in plan:
    if ONLY_TABLES and table not in ONLY_TABLES:
        continue
    df = read_source(fmt, path)
    df = df.toDF(*[clean_name(c) for c in df.columns])
    (df.write.mode("overwrite").option("overwriteSchema", True)
       .saveAsTable(q(catalog, source_schema, table)))
    n = spark.table(q(catalog, source_schema, table)).count()
    loaded_summary.append((table, fmt, len(df.columns), n))
    print(f"✅ {table}: {n:,} rows, {len(df.columns)} columns")

if loaded_summary:
    display(spark.createDataFrame(loaded_summary, "table string, format string, columns int, rows long"))

# COMMAND ----------

# MAGIC %md
# MAGIC **3e · Check the data contract (read-only).** This compares what's loaded with the contract that the attendee documents,
# MAGIC metric view template and app prompts use.
# MAGIC **Done when:** every table is ✅. A missing column is a ⚠️ warning. Either rename it in your file and re-run 3d, or update the
# MAGIC attendee docs and templates to match.

# COMMAND ----------

# Data contract: table -> columns the hackathon materials refer to (edit to match your final data)
DATA_CONTRACT = {
    "dim_date":            ["week_start_date", "fy_wk"],
    "dim_store":           ["store_id", "region", "rtl_grp"],
    "dim_product":         ["sku_id", "category", "brand"],
    "dim_supplier":        [],
    "dim_merchandiser":    [],
    "fact_sales_weekly":   ["store_id", "sku_id", "week_start_date", "nsv", "units", "margin", "promo_flag"],
    "fact_budget_monthly": [],
    "fact_promotions":     [],
    "fact_store_visits":   ["store_id", "osa_pct", "pog_comp"],
    "visit_notes":         ["note_text"],
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

PRIMARY_KEYS = {          # table -> [pk columns]   (matches 03_generate_synthetic_data; edit if you load your own data)
    "dim_date":          ["cal_date"],
    "dim_store":         ["store_id"],
    "dim_product":       ["sku_id"],
    "dim_supplier":      ["supplier_id"],
    "dim_merchandiser":  ["merchandiser_id"],
    "fact_promotions":   ["promo_id"],
    "fact_store_visits": ["visit_id"],
}
FOREIGN_KEYS = [          # (child table, [child cols], parent table, [parent cols])
    ("fact_sales_weekly", ["store_id"],        "dim_store",         ["store_id"]),
    ("fact_sales_weekly", ["sku_id"],          "dim_product",       ["sku_id"]),
    ("fact_sales_weekly", ["week_start_date"], "dim_date",          ["cal_date"]),
    ("dim_product",       ["supplier_id"],     "dim_supplier",      ["supplier_id"]),
    ("fact_promotions",   ["sku_id"],          "dim_product",       ["sku_id"]),
    ("fact_store_visits", ["store_id"],        "dim_store",         ["store_id"]),
    ("fact_store_visits", ["merchandiser_id"], "dim_merchandiser",  ["merchandiser_id"]),
    ("visit_notes",       ["visit_id"],        "fact_store_visits", ["visit_id"]),
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
    "fact_sales_weekly": {
        "_table": "Weekly sell-out (point-of-sale) sales. One row per store, SKU and week. Values in ZAR excl. VAT.",
        "store_id": "Store identifier. Joins to dim_store.store_id.",
        "sku_id": "Product (SKU) identifier. Joins to dim_product.sku_id.",
        "week_start_date": "First day (Monday) of the sales week.",
        "nsv": "Net sales value in ZAR excl. VAT, after discounts and returns. Also called sales, net sales or NSV. The default meaning of 'sales'.",
        "gsv": "Gross sales value in ZAR excl. VAT, before discounts. Also called gross sales or GSV.",
        "units": "Number of consumer units sold.",
        "margin": "Gross margin in ZAR (net sales value minus cost of goods).",
        "promo_flag": "Y if the SKU was on promotion in that store and week, N if it was at regular price.",
    },
    "dim_store": {
        "_table": "Store master. One row per store, with the retailer group and South African geography.",
        "store_id": "Store identifier.",
        "region": "Sales region (for example Gauteng North, Western Cape).",
        "rtl_grp": "Retailer group (the fictional retail chain the store belongs to). Also called retailer or chain.",
    },
    "dim_product": {
        "_table": "Product master. One row per SKU, with the category → subcategory → brand hierarchy.",
        "sku_id": "Product (SKU) identifier.",
        "category": "Product category (top level of the hierarchy).",
        "brand": "Brand name.",
    },
    "dim_date": {
        "_table": "Calendar. One row per day, with calendar and fiscal attributes. The fiscal year runs March to February.",
        "fy_wk": "Fiscal week number (1–52/53). Week 1 starts in March.",
    },
    "fact_store_visits": {
        "_table": "Merchandiser store visits. One row per visit, with in-store execution measures.",
        "osa_pct": "On-shelf availability %: share of the expected SKUs found on shelf during the visit (0–100). Target 85%. Also called OSA, availability or in-stock rate.",
        "pog_comp": "Planogram compliance %: share of the shelf that matches the agreed planogram (0–100). Also called POG compliance.",
    },
    "visit_notes": {
        "_table": "Free-text notes written by merchandisers during store visits. One row per note.",
        "note_text": "The merchandiser's comment in free text (for example 'shelf empty', 'display damaged').",
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

# 6c · reference metric view (answer key for Sprint 2). Column names follow the data contract; edit if yours differ.
MV_VERSION = "1.1"   # if your workspace rejects this, try "0.1"

def mv_sales_yaml(schema):
    return f"""
version: {MV_VERSION}
comment: "Weekly sell-out KPIs (reference)"
source: {catalog}.{schema}.fact_sales_weekly
joins:
  - name: store
    source: {catalog}.{schema}.dim_store
    on: source.store_id = store.store_id
  - name: product
    source: {catalog}.{schema}.dim_product
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
  - name: Promo Sales
    expr: SUM(source.nsv) FILTER (WHERE source.promo_flag = 'Y')
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
# MAGIC ## Step 8 · Dry run as a test team ⚠️ changes things
# MAGIC
# MAGIC Runs `01_team_setup` exactly as a team would, into `test_team_schema` (default `team_99`).
# MAGIC Ideally, **also** open `01_team_setup` yourself and run it by hand once, so you see what attendees see.
# MAGIC **Done when:** every row count matches and the constraints are present. Description coverage is low (expected).

# COMMAND ----------

result = dbutils.notebook.run("./01_team_setup", 900, {
    "catalog": catalog, "source_schema": source_schema,
    "team_schema": test_team_schema, "team_group": test_team_group,
})
print("01_team_setup finished", result or "")

display(spark.sql(f"SELECT table_name, constraint_type FROM {isc}.table_constraints WHERE table_schema = '{test_team_schema}' ORDER BY 1"))
for t in src_tables:
    s, d = spark.table(q(catalog, source_schema, t)).count(), spark.table(q(catalog, test_team_schema, t)).count()
    print(f"{'✅' if s == d else '❌'} {t}: source={s} team={d}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 9 · Test every sprint as an attendee (manual, about 60–90 min)
# MAGIC
# MAGIC Follow `docs/attendee-guide.md` with one scenario (Scenario D, Client Executive, covers the most tables), using `test_team_schema`. Time each step.
# MAGIC
# MAGIC | Sprint | Test | Pass when |
# MAGIC |---|---|---|
# MAGIC | 1 · Dashboard | Create a dashboard on the `team_99` tables, use the AI assistant for 3 visuals, add filters, publish | Published, and the AI assistant produces sensible charts |
# MAGIC | 2 · Metric views | Create `team_99.mv_sales` from the attendee-guide template (Appendix A), and query it with `MEASURE()` | The cell below returns rows, and the dashboard can use the metric view as a dataset |
# MAGIC | 3 · Genie baseline | Create a Genie space on the `team_99` tables, and ask the 10 Scenario D questions | You record a baseline. Expect several wrong answers (that's the point) |
# MAGIC | 4a · Descriptions | AI-generate the descriptions for 2 tables, then re-ask | The score goes up. If not, make the source less documented or the questions more ambiguous |
# MAGIC | 4a · Fallback | Run `02_apply_reference_descriptions` on `team_99` | Descriptions applied, and Genie improves further |
# MAGIC | 4b · Tuning | Add instructions (fiscal year, sales = NSV), sample questions, and the metric view | Final score ≥ 8/10 |
# MAGIC | 5 · AI Functions | Run the Scenario E `ai_classify` example on 100 notes | Sensible issue types |
# MAGIC | 5 · App (optional) | Create an app, then use the 2 Genie Code prompts (attendee guide, Appendix C) | Tab 1 table and Tab 2 visuals work. Note the time it took |
# MAGIC
# MAGIC Write down the **expected answers** to every scenario's 10 questions while you test, and save them as `docs/genie-test-answers.md` (facilitator only).

# COMMAND ----------

# Sprint 2 check: does the attendee template work on the test team schema?
try:
    spark.sql(f"CREATE OR REPLACE VIEW {q(catalog, test_team_schema, 'mv_sales')} WITH METRICS LANGUAGE YAML AS $${mv_sales_yaml(test_team_schema)}$$")
    display(spark.sql(f"SELECT Retailer, MEASURE(Sales) AS sales FROM {q(catalog, test_team_schema, 'mv_sales')} GROUP BY ALL ORDER BY sales DESC"))
except Exception as e:
    print(f"❌ The template failed on {test_team_schema}: {str(e)[:400]}\nUpdate attendee-guide Appendix A to match.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 10 · Cleanup of the test team ⚠️ destructive
# MAGIC
# MAGIC Drops **only** `test_team_schema` (and everything in it). It never touches the source or kit schemas.
# MAGIC To run it, type `DROP <test_team_schema>` (for example `DROP team_99`) into the **Cleanup confirmation** widget.
# MAGIC Delete any test dashboards, Genie spaces and apps by hand.
# MAGIC
# MAGIC *After the event:* drop each `team_XX` schema the same way, after agreeing with the customer what to keep.

# COMMAND ----------

confirm = dbutils.widgets.get("confirm_cleanup").strip()
if test_team_schema in (source_schema, kit_schema):
    raise ValueError("Refusing: test_team_schema is the same as the source or kit schema.")
if confirm == f"DROP {test_team_schema}":
    spark.sql(f"DROP SCHEMA IF EXISTS {TEST} CASCADE")
    print(f"🗑️  Dropped {TEST}")
else:
    print(f"Skipped. Type 'DROP {test_team_schema}' into the Cleanup confirmation widget to drop the test team schema.")
