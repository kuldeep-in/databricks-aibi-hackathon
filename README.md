# Databricks AI/BI Hackathon: Perfect Store Command Centre

A ready-to-run **4-hour hackathon** on Databricks covering **AI/BI Dashboards, Unity Catalog Metric Views, data descriptions, Genie**
and (optionally) **Databricks Apps built with Genie Code**.

> *You are the insights team at a fictional retail-execution agency. Your FMCG clients ask every Monday: how did we sell last week,
> did we hit budget, and what is happening on the shelf? Build the command centre that answers these questions.*

## Approach: quick win first, then make it better

| Area | Quick win | Improve | Prove it |
|---|---|---|---|
| Dashboards | Dashboard v1 straight on the tables | Rebuild on **metric views** | Same KPIs everywhere, less SQL |
| Genie | Genie space on undocumented tables (baseline score) | **Describe the data** in Unity Catalog, then add instructions, sample questions, SQL expressions, metric views, benchmarks | Score: baseline → after descriptions → final |
| App (optional) | Tab 1: data table | Tab 2: visuals | Built with Genie Code |

## Data model

One catalog, one **read-only source schema** (`hack_14oct`), and one schema per team (`team_01`…`team_05`). Each team **copies** the source
tables into its own schema, so it owns the data **and its descriptions**. A facilitator-only `facilitator_kit` schema holds the answer key.

## Repository layout

```
docs/
├── hackathon-plan.md          # facilitator plan: agenda, data strategy, metric views, Genie ladder, grants, rubric, risks
├── attendee-guide.md          # high-level attendee instructions, sprint by sprint, plus cheat-sheets
└── scenarios/                 # one instruction document per team scenario
    ├── A-supplier-account-manager.md
    ├── B-field-operations-manager.md
    ├── C-trade-marketing-manager.md
    ├── D-client-executive.md
    └── E-insights-analyst.md
notebooks/
├── 00_facilitator_runbook.py  # step-by-step setup and test: schemas, data load (Volume → hack_14oct), constraints, answer key, grants, dry run, cleanup
├── 01_team_setup.py           # run by each team: create team_XX and deep clone every table from hack_14oct
├── 02_apply_reference_descriptions.py  # facilitator fallback: apply the answer-key descriptions to a team schema
└── 03_generate_synthetic_data.py       # synthetic, fictional dataset generator (called from runbook Step 3)
```

## Getting started (facilitator)

1. Import `notebooks/` into your Databricks workspace (keep `docs/` alongside them), or clone this repo as a Git folder.
2. Open `00_facilitator_runbook`, set the `catalog` widget (the source schema defaults to `hack_14oct`), and run it **step by step**.
3. Step 3 generates the synthetic dataset into `hack_14oct` (default). Alternatively, load your own CSV/Parquet/JSON files (file name = table name).
4. Do a dry run as a test team (Step 8), then test every sprint (Step 9).
5. Fill in the placeholders in `docs/attendee-guide.md` (workspace URL, catalog, warehouses, notebook path) and share it with attendees.

> The data isn't included. Use **fictional** retailers, suppliers and brands only.
