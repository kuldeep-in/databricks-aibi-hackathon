# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Synthetic data generator: Perfect Store Command Centre
# MAGIC
# MAGIC Generates a **fully synthetic, fictional** retail-execution dataset straight into the source schema as Delta tables.
# MAGIC No real retailers, suppliers, brands or people. Usually called from **Step 3** of `00_facilitator_runbook`, but it can also be run on its own.
# MAGIC
# MAGIC | Table | Grain | Default size |
# MAGIC |---|---|---|
# MAGIC | `dim_date` | day (calendar + fiscal year March–February) | ~1,100 |
# MAGIC | `dim_store` | store (South African regions, fictional retailer groups) | 120 |
# MAGIC | `dim_supplier` | supplier (category type Food / Liquor / GM) | 22 |
# MAGIC | `dim_product` | SKU (category → subcategory → brand) | 200 |
# MAGIC | `dim_merchandiser` | field rep | ~20 |
# MAGIC | `fact_promotions` | promotion × SKU × retailer group | ~1,000 |
# MAGIC | `fact_sales_weekly` | week × store × SKU (ZAR, excl. VAT) | ~350K |
# MAGIC | `fact_budget_monthly` | month × region × retailer group × category | ~10K |
# MAGIC | `fact_store_visits` | merchandiser visit (OSA %, POG compliance %, share of shelf %) | ~30K |
# MAGIC | `visit_notes` | free-text merchandiser note | ~9K |
# MAGIC
# MAGIC **Insights planted in the data** (facilitator only, so don't share them with attendees):
# MAGIC 1. **Execution gap:** in region **KZN Inland**, OSA falls from about 90% to about 75% over the last 26 weeks, and sales drop with it. The region ends up below budget.
# MAGIC 2. **Loss-making promotion:** the *Buy 2 Get 1 Free* mechanic has the biggest uplift but **negative margin**. *20% Off* and *Bundle Deal* are profitable.
# MAGIC 3. **Seasonality:** a December peak (Liquor even more), a summer lift for soft drinks, an Easter lift, and a month-end payday bump.
# MAGIC 4. **Share shift:** supplier **Oryx Beverages** gains about 30% a year, while **Amber Valley Beverages** declines.
# MAGIC 5. **Visit frequency drives compliance:** stores visited more often have higher planogram compliance.
# MAGIC 6. **Coverage gap:** about 4% of stores haven't been visited in the last 4 weeks.
# MAGIC 7. **Visit notes:** out-of-stock notes cluster where OSA is low, and competitor-activity notes increase over time.
# MAGIC
# MAGIC **Column names are deliberately imperfect**, like a real source system: abbreviated and inconsistent (`str_id`, `sku`, `qty`, `nsv`, `gp`,
# MAGIC `prm_flg`, `wk_strt_dt`, `rgn`, `fmt_cd`, `osa_pct`, `nt_txt`), with **coded values** (`fmt_cd` HYP/SUP/CNV/WHS, `sts` O/C,
# MAGIC `tier_cd` K/C/E, `cat_typ` FD/LQ/GM, `prm_typ` PR/MB/BN, `prm_flg` Y/N). **No descriptions are written.** Attendees add them in
# MAGIC Sprint 4a and build metric views in Sprint 2 to get good results. The full column dictionary is the `RENAMES` map below.
# MAGIC The data is **deterministic** for a given seed, and it ends with the last complete week before the run date.

# COMMAND ----------

dbutils.widgets.text("catalog", "<your_catalog>", "1. Catalog")

# COMMAND ----------

import random, datetime as dt
from pyspark.sql import functions as F

catalog = dbutils.widgets.get("catalog").strip()
schema = "hack_14oct"   # target (source) schema

# Fixed sizes (edit here if needed)
N_STORES = 120       # stores
N_SKUS = 200         # SKUs
N_WEEKS = 156        # weeks of history (3 years)
RANGING = 0.10       # share of SKUs ranged per store  → ~350K weekly sales rows
SEED = 42            # same seed = same data
rng = random.Random(SEED)

DROP_REGION = "KZN Inland"     # insight 1
DROP_WEEKS = 26
GROWTH_SUPPLIER, DECLINE_SUPPLIER = "Oryx Beverages", "Amber Valley Beverages"   # insight 4

today = dt.date.today()
END_WEEK = today - dt.timedelta(days=today.weekday() + 7)          # Monday of the last complete week
START_WEEK = END_WEEK - dt.timedelta(weeks=N_WEEKS - 1)
print(f"Target {catalog}.{schema} · weeks {START_WEEK} → {END_WEEK} · {N_STORES} stores · {N_SKUS} SKUs")

def tbl(name):
    return f"`{catalog}`.`{schema}`.`{name}`"

# Source-system style column names: abbreviated and inconsistent ON PURPOSE, so attendees have to describe the
# data (Sprint 4a) and build metric views (Sprint 2) before dashboards and Genie give good answers.
RENAMES = {
    "dim_date": {"cal_date": "dt", "date_key": "dt_key", "week_start_date": "wk_strt_dt", "cal_year": "cal_yr", "cal_qtr": "cal_q",
                 "cal_month": "cal_mth", "month_name": "mth_nm", "day_name": "dy_nm", "is_weekend": "wknd_flg",
                 "fy": "fy_cd", "fy_month": "fy_mth", "fy_qtr": "fy_q", "fy_wk": "fy_wk"},
    "dim_store": {"store_id": "str_id", "store_code": "str_cd", "store_name": "str_nm", "rtl_grp": "rtl_grp", "banner": "bnr",
                  "store_format": "fmt_cd", "region": "rgn", "province": "prov", "city": "cty", "lat": "lat", "lon": "lng",
                  "open_date": "opn_dt", "store_status": "sts"},
    "dim_merchandiser": {"merchandiser_id": "rep_id", "rep_name": "rep_nm", "team_lead": "tl_nm", "region": "rgn", "start_date": "strt_dt"},
    "dim_supplier": {"supplier_id": "supp_id", "supplier_name": "supp_nm", "supplier_tier": "tier_cd", "category_type": "cat_typ"},
    "dim_product": {"sku_id": "sku", "sku_code": "sku_cd", "sku_name": "sku_desc", "brand": "brnd", "supplier_id": "supp_id",
                    "category": "cat", "subcategory": "sub_cat", "pack_size": "pk_sz", "list_price": "rsp"},
    "fact_promotions": {"promo_id": "prm_id", "promo_name": "prm_desc", "mechanic": "mech", "promo_type": "prm_typ",
                        "discount_pct": "disc", "sku_id": "sku", "rtl_grp": "rtl_grp", "start_date": "strt_dt", "end_date": "end_dt"},
    "fact_sales_weekly": {"week_start_date": "wk_strt_dt", "store_id": "str_id", "sku_id": "sku", "units": "qty", "gsv": "gsv",
                          "nsv": "nsv", "cost": "cogs", "margin": "gp", "promo_flag": "prm_flg", "promo_id": "prm_id"},
    "fact_budget_monthly": {"month_start_date": "mth_strt_dt", "region": "rgn", "rtl_grp": "rtl_grp", "category": "cat", "budget_nsv": "bgt_nsv"},
    "fact_store_visits": {"visit_id": "vst_id", "visit_date": "vst_dt", "store_id": "str_id", "merchandiser_id": "rep_id",
                          "duration_min": "dur", "osa_pct": "osa_pct", "pog_comp": "pog_comp", "sos_pct": "sos"},
    "visit_notes": {"note_id": "nt_id", "visit_id": "vst_id", "store_id": "str_id", "merchandiser_id": "rep_id",
                    "note_date": "nt_dt", "note_text": "nt_txt"},
}

def save(df, name):
    for old, new in RENAMES.get(name, {}).items():
        if old != new:
            df = df.withColumnRenamed(old, new)
    df.write.mode("overwrite").option("overwriteSchema", True).saveAsTable(tbl(name))
    print(f"✅ {name}: {spark.table(tbl(name)).count():,} rows")

def L(label):
    """SQL string literal for a hash label (keeps quotes out of f-string expressions)."""
    return "'" + label + "'"

def u(*parts):
    """Deterministic uniform [0,1) as a SQL expression, hashed from columns and labels (stable across runs and partitions)."""
    return f"(pmod(xxhash64({', '.join(parts)}, {SEED}), 1000000) / 1000000.0)"

# COMMAND ----------

# MAGIC %md
# MAGIC ## dim_date (calendar and fiscal year March–February)

# COMMAND ----------

dim_date = spark.sql(f"""
    SELECT d AS cal_date,
           CAST(date_format(d, 'yyyyMMdd') AS INT)                   AS date_key,
           CAST(date_trunc('week', d) AS DATE)                       AS week_start_date,
           year(d) AS cal_year, quarter(d) AS cal_qtr, month(d) AS cal_month,
           date_format(d, 'MMMM') AS month_name, date_format(d, 'EEEE') AS day_name,
           dayofweek(d) IN (1, 7)                                    AS is_weekend,
           concat('FY', CAST(fy_start_year + 1 AS STRING))           AS fy,
           pmod(month(d) + 9, 12) + 1                                AS fy_month,
           CAST(ceil((pmod(month(d) + 9, 12) + 1) / 3.0) AS INT)     AS fy_qtr,
           CAST(floor(datediff(d, make_date(fy_start_year, 3, 1)) / 7) + 1 AS INT) AS fy_wk
    FROM (SELECT d, IF(month(d) >= 3, year(d), year(d) - 1) AS fy_start_year
          FROM (SELECT explode(sequence(DATE'{START_WEEK}', DATE'{END_WEEK + dt.timedelta(days=6)}', INTERVAL 1 DAY)) AS d))
""")
save(dim_date, "dim_date")
# fy = 'FY2027' covers 1 Mar 2026 – 28 Feb 2027 (named after the year in which it ends)

# COMMAND ----------

# MAGIC %md
# MAGIC ## dim_store, dim_merchandiser

# COMMAND ----------

REGIONS = {   # region: (weight, [(city, province, lat, lon)])
    "Gauteng North": (0.14, [("Pretoria", "Gauteng", -25.75, 28.19), ("Centurion", "Gauteng", -25.86, 28.19), ("Soshanguve", "Gauteng", -25.52, 28.10)]),
    "Gauteng South": (0.20, [("Johannesburg", "Gauteng", -26.20, 28.05), ("Soweto", "Gauteng", -26.27, 27.86), ("Germiston", "Gauteng", -26.22, 28.17), ("Vereeniging", "Gauteng", -26.67, 27.93)]),
    "Western Cape":  (0.17, [("Cape Town", "Western Cape", -33.92, 18.42), ("Stellenbosch", "Western Cape", -33.93, 18.86), ("George", "Western Cape", -33.96, 22.46), ("Paarl", "Western Cape", -33.73, 18.96)]),
    "KZN Coastal":   (0.10, [("Durban", "KwaZulu-Natal", -29.86, 31.02), ("Umhlanga", "KwaZulu-Natal", -29.73, 31.08), ("Port Shepstone", "KwaZulu-Natal", -30.74, 30.45)]),
    "KZN Inland":    (0.08, [("Pietermaritzburg", "KwaZulu-Natal", -29.60, 30.38), ("Newcastle", "KwaZulu-Natal", -27.76, 29.93), ("Ladysmith", "KwaZulu-Natal", -28.56, 29.78)]),
    "Eastern Cape":  (0.10, [("Gqeberha", "Eastern Cape", -33.96, 25.60), ("East London", "Eastern Cape", -33.02, 27.91), ("Mthatha", "Eastern Cape", -31.59, 28.78)]),
    "Central":       (0.11, [("Bloemfontein", "Free State", -29.12, 26.21), ("Rustenburg", "North West", -25.67, 27.24), ("Kimberley", "Northern Cape", -28.74, 24.77)]),
    "Northern":      (0.10, [("Polokwane", "Limpopo", -23.90, 29.47), ("Mbombela", "Mpumalanga", -25.47, 30.97), ("eMalahleni", "Mpumalanga", -25.87, 29.23)]),
}
RETAILERS = {   # retailer group: (weight, [(banner, format)])
    "Kestrel Retail Group": (0.28, [("Kestrel Hyper", "Hyper"), ("Kestrel Super", "Super")]),
    "Baobab Stores":        (0.24, [("Baobab", "Super"), ("Baobab Express", "Convenience")]),
    "Protea Hypermarkets":  (0.14, [("Protea Hyper", "Hyper")]),
    "Savanna Fresh":        (0.18, [("Savanna Fresh", "Super")]),
    "Umoya Wholesale":      (0.16, [("Umoya Cash & Carry", "Wholesale")]),
}
FORMAT = {"Hyper": (3.0, 1.6), "Super": (1.5, 1.0), "Convenience": (0.6, 0.5), "Wholesale": (2.2, 0.8)}   # (size factor, range factor)
FORMAT_CD = {"Hyper": "HYP", "Super": "SUP", "Convenience": "CNV", "Wholesale": "WHS"}        # saved as codes

FIRST = ["Thabo", "Lerato", "Sipho", "Ayanda", "Pieter", "Annelie", "Nomsa", "Kagiso", "Zanele", "Johan", "Fatima", "Ravi", "Precious",
         "Bongani", "Lindiwe", "Themba", "Karabo", "Naledi", "Mandla", "Chloe", "Ruan", "Yusuf", "Palesa", "Tshepo"]
LAST = ["Dlamini", "Nkosi", "van der Merwe", "Botha", "Naidoo", "Mokoena", "Khumalo", "Pillay", "Mahlangu", "Jacobs", "Ndlovu", "Smit",
        "Mthembu", "Pretorius", "Govender", "Zulu", "Maseko", "Coetzee", "Adams", "Sithole"]

region_names = list(REGIONS)
reps, reps_by_region, used_names = [], {}, set()
for region in region_names:
    n_reps = max(2, round(N_STORES * REGIONS[region][0] / 6))
    for i in range(n_reps):
        while True:
            name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
            if name not in used_names:
                used_names.add(name); break
        reps.append([len(reps) + 1, name, None, region, START_WEEK - dt.timedelta(days=rng.randint(30, 2000))])
        reps_by_region.setdefault(region, []).append(len(reps))
for region, ids in reps_by_region.items():          # first rep of each region is the team lead
    lead = reps[ids[0] - 1][1]
    for rid in ids:
        reps[rid - 1][2] = lead

stores, store_x, name_count = [], [], {}
for sid in range(1, N_STORES + 1):
    region = rng.choices(region_names, weights=[REGIONS[r][0] for r in region_names])[0]
    city, province, lat, lon = rng.choice(REGIONS[region][1])
    grp = rng.choices(list(RETAILERS), weights=[RETAILERS[g][0] for g in RETAILERS])[0]
    banner, fmt = rng.choice(RETAILERS[grp][1])
    base = f"{banner} {city}"
    name_count[base] = name_count.get(base, 0) + 1
    name = base if name_count[base] == 1 else f"{base} {name_count[base]}"
    status = "O" if rng.random() > 0.03 else "C"
    stores.append((sid, f"S{sid:05d}", name, grp, banner, FORMAT_CD[fmt], region, province, city,
                   round(lat + rng.uniform(-0.12, 0.12), 5), round(lon + rng.uniform(-0.12, 0.12), 5),
                   START_WEEK - dt.timedelta(days=rng.randint(200, 6000)), status))
    size, rangef = FORMAT[fmt]
    store_x.append((sid, grp, region, size * rng.uniform(0.7, 1.3), rangef, rng.uniform(86, 96),
                    rng.uniform(0.5, 2.8), rng.random() < 0.04, rng.choice(reps_by_region[region])))

save(spark.createDataFrame(stores, "store_id INT, store_code STRING, store_name STRING, rtl_grp STRING, banner STRING, store_format STRING, "
                                   "region STRING, province STRING, city STRING, lat DOUBLE, lon DOUBLE, open_date DATE, store_status STRING"), "dim_store")
save(spark.createDataFrame([tuple(r) for r in reps], "merchandiser_id INT, rep_name STRING, team_lead STRING, region STRING, start_date DATE"), "dim_merchandiser")

# internal store attributes used only to generate facts (not saved)
stores_x = spark.createDataFrame(store_x, "store_id INT, rtl_grp STRING, region STRING, size_factor DOUBLE, range_factor DOUBLE, "
                                          "exec_base DOUBLE, visit_freq DOUBLE, coverage_gap BOOLEAN, merchandiser_id INT")

# COMMAND ----------

# MAGIC %md
# MAGIC ## dim_supplier, dim_product

# COMMAND ----------

CATS = {   # category: (category type, subcategories, price range, cost ratio, base weekly units, pack sizes)
    "Snacks":        ("Food",   ["Chips", "Biscuits", "Nuts"],              (15, 45),   0.62, 6.0, ["125g", "150g", "250g"]),
    "Soft Drinks":   ("Food",   ["Carbonated", "Juice", "Water"],           (12, 35),   0.60, 9.0, ["330ml", "500ml", "2L"]),
    "Dairy":         ("Food",   ["Milk", "Yoghurt", "Cheese"],              (18, 90),   0.70, 7.0, ["1L", "500g", "2L"]),
    "Breakfast":     ("Food",   ["Cereal", "Oats", "Spreads"],              (30, 80),   0.65, 4.0, ["500g", "750g", "1kg"]),
    "Beer":          ("Liquor", ["Lager", "Craft"],                         (18, 120),  0.72, 5.0, ["6x330ml", "440ml", "750ml"]),
    "Cider":         ("Liquor", ["Apple", "Flavoured"],                     (20, 110),  0.70, 3.0, ["6x330ml", "500ml"]),
    "Spirits":       ("Liquor", ["Brandy", "Gin", "Whisky", "Vodka"],       (150, 450), 0.75, 1.2, ["750ml", "1L"]),
    "Personal Care": ("GM",     ["Soap", "Deodorant", "Hair Care"],         (20, 110),  0.55, 2.5, ["150ml", "250ml", "400ml"]),
    "Household":     ("GM",     ["Detergent", "Cleaning", "Paper"],         (25, 140),  0.60, 3.0, ["750ml", "1.5L", "2kg"]),
}
SUPPLIERS = [   # (name, tier, categories, yearly trend)
    ("Kudu Ridge Foods", "Key", ["Snacks", "Breakfast"], 0.03), ("Karoo Snacks Co", "Core", ["Snacks"], 0.02),
    ("Zebra Snack Foods", "Emerging", ["Snacks"], 0.06), ("Golden Kernel Mills", "Core", ["Breakfast"], 0.01),
    ("Sunrise Cereals", "Core", ["Breakfast"], 0.00), ("Indigo Dairy", "Key", ["Dairy"], 0.02),
    ("Pebble Bay Dairy", "Core", ["Dairy"], 0.03), (GROWTH_SUPPLIER, "Emerging", ["Soft Drinks"], 0.30),
    (DECLINE_SUPPLIER, "Key", ["Soft Drinks"], -0.10), ("Orchard Ridge Beverages", "Core", ["Soft Drinks"], 0.02),
    ("Kalahari Kitchen", "Emerging", ["Snacks", "Dairy"], 0.05), ("Blue Crane Brewing", "Key", ["Beer"], 0.02),
    ("Riverbend Brewing", "Emerging", ["Beer"], 0.08), ("Fynbos Cider Works", "Core", ["Cider"], 0.04),
    ("Kloof Peak Distillers", "Key", ["Spirits"], 0.01), ("Marula Grove Spirits", "Core", ["Spirits"], 0.03),
    ("Mopane Spirits", "Emerging", ["Spirits", "Cider"], 0.05), ("Clearwater Home Care", "Key", ["Household"], 0.01),
    ("Lionsgate Household", "Core", ["Household"], 0.02), ("Starling Home Products", "Core", ["Household", "Personal Care"], 0.02),
    ("Silk & Rose Personal Care", "Key", ["Personal Care"], 0.03), ("Aloe Grove Personal Care", "Emerging", ["Personal Care"], 0.06),
]
ADJ = ["Sunny", "Crisp", "Golden", "Wild", "Urban", "Royal", "Happy", "Fresh", "Bold", "Pure", "Velvet", "Rustic", "Bright", "Silver", "Little", "Big"]
NOUN = ["Kudu", "Baobab", "Lynx", "Hornbill", "Springbok", "Meerkat", "Protea", "Ember", "Harvest", "River", "Summit", "Dune", "Willow", "Falcon", "Pebble", "Breeze"]
VARIANTS = ["Original", "Lite", "Classic", "Premium", "Spicy", "Zero", "Family", "Select"]

brand_pool = rng.sample([f"{a} {n}" for a in ADJ for n in NOUN], k=len(SUPPLIERS) * 4)
suppliers, brands_of = [], {}
for i, (name, tier, cats, trend) in enumerate(SUPPLIERS, start=1):
    suppliers.append((i, name, tier[0], {"Food": "FD", "Liquor": "LQ", "GM": "GM"}[CATS[cats[0]][0]]))
    brands_of[i] = brand_pool[(i - 1) * 4:(i - 1) * 4 + rng.randint(2, 4)]
save(spark.createDataFrame(suppliers, "supplier_id INT, supplier_name STRING, supplier_tier STRING, category_type STRING"), "dim_supplier")

products, product_x, seen = [], [], set()
weights = [{"Key": 3, "Core": 2, "Emerging": 1}[s[1]] for s in SUPPLIERS]
for sku in range(1, N_SKUS + 1):
    sidx = rng.choices(range(len(SUPPLIERS)), weights=weights)[0]
    sname, _, scats, strend = SUPPLIERS[sidx]
    cat = rng.choice(scats)
    ctype, subs, (pmin, pmax), cost, base, packs = CATS[cat]
    brand, sub, pack = rng.choice(brands_of[sidx + 1]), rng.choice(subs), rng.choice(packs)
    name = f"{brand} {sub} {pack}"
    while name in seen:
        name = f"{brand} {sub} {rng.choice(VARIANTS)} {pack}"
    seen.add(name)
    price = round(rng.uniform(pmin, pmax)) - 0.01
    products.append((sku, f"P{sku:05d}", name, brand, sidx + 1, cat, sub, pack, price))
    product_x.append((sku, cat, price, min(0.85, max(0.45, cost + rng.uniform(-0.05, 0.05))),
                      base * rng.uniform(0.4, 1.8), strend + rng.uniform(-0.02, 0.02)))

save(spark.createDataFrame(products, "sku_id INT, sku_code STRING, sku_name STRING, brand STRING, supplier_id INT, category STRING, "
                                     "subcategory STRING, pack_size STRING, list_price DOUBLE"), "dim_product")
products_x = spark.createDataFrame(product_x, "sku_id INT, category STRING, list_price DOUBLE, cost_ratio DOUBLE, base_units DOUBLE, trend DOUBLE")

# COMMAND ----------

# MAGIC %md
# MAGIC ## fact_promotions

# COMMAND ----------

MECHANICS = [   # (mechanic, promo type, discount %, uplift, weight). Buy 2 Get 1 Free = high uplift, negative margin (insight 2)
    ("10% Off", "PR", 10.0, 1.15, 3), ("20% Off", "PR", 20.0, 1.45, 3),      # prm_typ codes: PR price reduction,
    ("Buy 2 Get 1 Free", "MB", 33.3, 1.95, 2), ("Multi-buy 2 for", "MB", 25.0, 1.60, 2),   # MB multi-buy, BN bundle
    ("Bundle Deal", "BN", 15.0, 1.50, 2),
]
retailer_names = list(RETAILERS)
promos = []
for pid in range(1, N_SKUS * 5 + 1):
    mech, ptype, disc, uplift, _ = rng.choices(MECHANICS, weights=[m[4] for m in MECHANICS])[0]
    start = START_WEEK + dt.timedelta(weeks=rng.randint(0, N_WEEKS - 2))
    length = rng.randint(2, 4)
    sku = rng.randint(1, N_SKUS)
    grp = rng.choice(retailer_names)
    promos.append((pid, f"{grp.split()[0]} {mech} – {products[sku - 1][3]}", mech, ptype, disc, sku, grp,
                   start, min(END_WEEK + dt.timedelta(days=6), start + dt.timedelta(weeks=length, days=-1)), uplift))

promos_df = spark.createDataFrame(promos, "promo_id INT, promo_name STRING, mechanic STRING, promo_type STRING, discount_pct DOUBLE, "
                                          "sku_id INT, rtl_grp STRING, start_date DATE, end_date DATE, uplift DOUBLE")
save(promos_df.drop("uplift"), "fact_promotions")

promo_weeks = (promos_df
    .withColumn("week_start_date", F.explode(F.expr("sequence(start_date, end_date, INTERVAL 7 DAY)")))
    .groupBy("sku_id", "rtl_grp", "week_start_date")
    .agg(F.min(F.struct("promo_id", "discount_pct", "uplift")).alias("p"))
    .select("sku_id", "rtl_grp", "week_start_date", "p.promo_id", "p.discount_pct", "p.uplift"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## fact_sales_weekly, fact_budget_monthly

# COMMAND ----------

EASTER = [dt.date(2023, 4, 9), dt.date(2024, 3, 31), dt.date(2025, 4, 20), dt.date(2026, 4, 5), dt.date(2027, 3, 28), dt.date(2028, 4, 16)]
weeks = [(i, START_WEEK + dt.timedelta(weeks=i)) for i in range(N_WEEKS)]
weeks_df = spark.createDataFrame(
    [(i, w, any(e - dt.timedelta(days=13) <= w <= e - dt.timedelta(days=1) for e in EASTER)) for i, w in weeks],
    "week_idx INT, week_start_date DATE, easter BOOLEAN")

OSA_LATENT = f"""(exec_base
    - CASE WHEN region = '{DROP_REGION}' AND week_idx >= {N_WEEKS - DROP_WEEKS}
           THEN least(16.0, (week_idx - {N_WEEKS - DROP_WEEKS} + 1) * 4.0) ELSE 0 END
    + ({u('store_id', 'week_idx', L('osa'))} - 0.5) * 6)"""

SEASON = """(CASE month(week_start_date) WHEN 12 THEN 1.35 WHEN 11 THEN 1.10 WHEN 1 THEN 0.88 ELSE 1.0 END
    * CASE WHEN category IN ('Beer', 'Cider', 'Spirits') AND month(week_start_date) IN (12, 1) THEN 1.25 ELSE 1.0 END
    * CASE WHEN category = 'Soft Drinks' AND month(week_start_date) IN (11, 12, 1, 2) THEN 1.15
           WHEN category = 'Soft Drinks' AND month(week_start_date) IN (6, 7) THEN 0.88 ELSE 1.0 END
    * CASE WHEN easter THEN 1.15 ELSE 1.0 END
    * CASE WHEN day(week_start_date) >= 22 OR day(week_start_date) <= 3 THEN 1.06 ELSE 1.0 END)"""

pairs = (stores_x.crossJoin(products_x)
         .where(f"{u('store_id', 'sku_id', L('rng'))} < least(0.95, {RANGING} * range_factor)"))

sales_x = (pairs.crossJoin(weeks_df)
    .join(promo_weeks, ["sku_id", "rtl_grp", "week_start_date"], "left")
    .withColumn("exec_factor", F.expr(f"1 - greatest(0, 90 - {OSA_LATENT}) * 0.015"))
    .withColumn("price", F.expr("list_price * power(1.06, week_idx / 52.0)"))
    .withColumn("units", F.expr(f"""CAST(greatest(0, round(base_units * size_factor * {SEASON}
                                    * power(1 + trend, week_idx / 52.0) * exec_factor * coalesce(uplift, 1.0)
                                    * (0.6 + 0.8 * ({u('store_id', 'sku_id', 'week_idx', L('n1'))} + {u('store_id', 'sku_id', 'week_idx', L('n2'))}) / 2))) AS INT)"""))
    .where("units > 0")
    .withColumn("gsv", F.expr("CAST(round(units * price, 2) AS DECIMAL(14,2))"))
    .withColumn("nsv", F.expr("CAST(round(units * price * (1 - coalesce(discount_pct, 0) / 100 - 0.03), 2) AS DECIMAL(14,2))"))
    .withColumn("cost", F.expr("CAST(round(units * price * cost_ratio, 2) AS DECIMAL(14,2))"))
    .withColumn("margin", F.expr("nsv - cost"))
    .withColumn("promo_flag", F.expr("IF(promo_id IS NULL, 'N', 'Y')")))

save(sales_x.select("week_start_date", "store_id", "sku_id", "units", "gsv", "nsv", "cost", "margin", "promo_flag", "promo_id"),
     "fact_sales_weekly")

# Budget = what sales would have been without the execution gap, plus a ~3% growth target, so the OSA-drop region lands below budget
budget = (sales_x
    .withColumn("month_start_date", F.expr("CAST(trunc(week_start_date, 'MM') AS DATE)"))
    .groupBy("month_start_date", "region", "rtl_grp", "category")
    .agg(F.expr("sum(nsv / exec_factor)").alias("base_nsv"))
    .withColumn("budget_nsv", F.expr(f"CAST(round(base_nsv * (1.03 + ({u('month_start_date', 'region', 'rtl_grp', 'category', L('bud'))} - 0.5) * 0.08), 2) AS DECIMAL(16,2))"))
    .drop("base_nsv"))
save(budget, "fact_budget_monthly")

# COMMAND ----------

# MAGIC %md
# MAGIC ## fact_store_visits, visit_notes

# COMMAND ----------

visits_x = (stores_x.crossJoin(weeks_df).crossJoin(spark.range(3).withColumnRenamed("id", "slot"))
    .where(f"{u('store_id', 'week_idx', 'slot', L('v'))} < visit_freq / 3")
    .where(f"NOT (coverage_gap AND week_idx >= {N_WEEKS - 4})")
    .withColumn("visit_id", F.expr("CAST(store_id AS BIGINT) * 100000 + week_idx * 10 + slot"))
    .withColumn("visit_date", F.expr(f"date_add(week_start_date, CAST({u('store_id', 'week_idx', 'slot', L('d'))} * 6 AS INT))"))
    .withColumn("duration_min", F.expr(f"CAST(15 + size_factor * 12 + {u('visit_id', L('dur'))} * 20 AS INT)"))
    .withColumn("osa_pct", F.expr(f"round(least(100, greatest(40, {OSA_LATENT} + ({u('visit_id', L('o'))} - 0.5) * 8)), 1)"))
    .withColumn("pog_comp", F.expr(f"""round(least(100, greatest(25, 52 + visit_freq * 13 + ({u('visit_id', L('p'))} - 0.5) * 18
                                       - CASE WHEN region = '{DROP_REGION}' AND week_idx >= {N_WEEKS - DROP_WEEKS} THEN 6 ELSE 0 END)), 1)"""))
    .withColumn("sos_pct", F.expr(f"round(12 + {u('visit_id', L('s'))} * 28, 1)")))

save(visits_x.select("visit_id", "visit_date", "store_id", "merchandiser_id", "duration_min", "osa_pct", "pog_comp", "sos_pct"),
     "fact_store_visits")

TEMPLATES = {
    "oos":   ["Shelf empty for {c}, no stock in the back room either.", "Out of stock on most {c} lines, store manager says the order was short-delivered.",
              "Gaps on the {c} shelf, only a few facings filled.", "No stock of {c} again this week. Raised with the receiving clerk.",
              "OOS on top-selling {c} SKUs, replenishment delayed."],
    "dmg":   ["Promotional display for {c} is damaged and leaning, needs replacing.", "Gondola end for {c} broken, stock placed on the floor.",
              "Shelf strip on the {c} bay is cracked."],
    "price": ["Price tags missing on half of the {c} shelf.", "Wrong price shown on the {c} promo ticket.",
              "No promo pricing displayed for {c} although the promo is live."],
    "pog":   ["{c} not merchandised to planogram, competitor products in our space.", "Planogram reset needed for {c}, facings mixed up.",
              "Store moved {c} to a lower shelf without approval."],
    "comp":  ["Competitor running an aggressive in-store promotion on {c}.", "New competitor display installed next to our {c} bay.",
              "Competitor merchandiser took extra facings in {c}."],
    "ok":    ["All good, {c} fully stocked and to planogram.", "Great display for {c}, store manager very happy.",
              "Shelf looks perfect, {c} promo well executed."],
}
CAT_WORDS = ["chips", "soft drinks", "yoghurt", "cereal", "beer", "cider", "gin", "deodorant", "washing powder", "biscuits"]

def sql_array(xs):
    return "array(" + ", ".join("'" + x.replace("'", "\\'") + "'" for x in xs) + ")"

def pick(kind):
    xs = TEMPLATES[kind]
    return f"element_at({sql_array(xs)}, CAST({u('visit_id', L('t'))} * {len(xs)} AS INT) + 1)"

comp_p = f"(0.04 + 0.14 * week_idx / {N_WEEKS})"   # competitor activity grows over time (insight 7)
r = u("visit_id", L('k'))
notes = (visits_x.where(f"{u('visit_id', L('note'))} < 0.30")
    .withColumn("kind", F.expr(f"""CASE
        WHEN osa_pct < 80 AND {r} < 0.7 THEN 'oos'
        WHEN {u('visit_id', L('k2'))} < {comp_p} THEN 'comp'
        WHEN {u('visit_id', L('k2'))} < {comp_p} + 0.10 THEN 'oos'
        WHEN {u('visit_id', L('k2'))} < {comp_p} + 0.22 THEN 'dmg'
        WHEN {u('visit_id', L('k2'))} < {comp_p} + 0.37 THEN 'price'
        WHEN {u('visit_id', L('k2'))} < {comp_p} + 0.52 THEN 'pog'
        ELSE 'ok' END"""))
    .withColumn("template", F.expr("CASE kind " + " ".join(f"WHEN '{k}' THEN {pick(k)}" for k in TEMPLATES) + " END"))
    .withColumn("cat_word", F.expr(f"element_at({sql_array(CAT_WORDS)}, CAST({u('visit_id', L('c'))} * {len(CAT_WORDS)} AS INT) + 1)"))
    .withColumn("note_text", F.expr("replace(template, '{c}', cat_word)"))
    .withColumn("note_id", F.expr("visit_id * 10 + 1")))

save(notes.select("note_id", "visit_id", "store_id", "merchandiser_id", F.col("visit_date").alias("note_date"), "note_text"), "visit_notes")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

display(spark.sql(f"""
    SELECT table_name, table_type FROM `{catalog}`.information_schema.tables
    WHERE table_schema = '{schema}' ORDER BY table_name
"""))
dbutils.notebook.exit(f"generated {catalog}.{schema}: weeks {START_WEEK}..{END_WEEK}")
