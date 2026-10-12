# Databricks AI/BI Hackathon: Perfect Store Command Centre

A ready-to-run **4-hour hackathon** on Databricks covering **AI/BI Dashboards, Unity Catalog Metric Views, data descriptions, Genie**
and **Databricks Apps built with Genie Code**.

> *You are the insights team at a fictional retail-execution agency. Your FMCG clients ask every Monday: how did we sell last week,
> did we hit budget, and what is happening on the shelf? Build the command centre that answers these questions.*

## Approach: quick win first, then make it better

| Area | Quick win | Improve | Prove it |
|---|---|---|---|
| Dashboards | Dashboard v1 straight on the tables | Rebuild on **metric views** | Same KPIs everywhere, less SQL |
| Genie | Genie space on undocumented tables (baseline score) | **Describe the data** in Unity Catalog, then add instructions, sample questions, SQL expressions, metric views, benchmarks | Score: baseline → after descriptions → final |
| App | Tab 1: data table | Tab 2: visuals | Built with Genie Code |

## Data model

One catalog, one **read-only source schema** (`hack_14oct`), and **one schema per attendee**, which they create themselves. Each attendee **copies** the source
tables into their own schema, so they own the data **and its descriptions**.

## Repository layout

```
docs/
├── hackathon-plan.md          # facilitator plan: agenda, data strategy, metric views, Genie ladder, grants, rubric, risks
├── attendee-guide.md          # high-level attendee instructions, sprint by sprint, plus cheat-sheets
└── scenario.md                # the one scenario everyone builds (Monday Command Centre)
notebooks/
├── 00_facilitator_runbook.py  # step-by-step setup and test: schemas, synthetic data as Delta tables in hack_14oct, constraints, grants, testing
├── 01_attendee_setup.py       # run by every attendee: create their own schema, then deep clone every table from hack_14oct
└── 02_generate_synthetic_data.py  # synthetic, fictional dataset generator (called from runbook Step 3)
```

## Getting started (facilitator)

1. Import `notebooks/` into your Databricks workspace (keep `docs/` alongside them), or clone this repo as a Git folder.
2. Open `00_facilitator_runbook`, set the `catalog` widget (the source schema defaults to `hack_14oct`), and run it **step by step**.
3. Step 3 generates the synthetic dataset as Delta tables in `hack_14oct`. Make that schema read-only for participants.
4. Test as an attendee (Step 8): run `01_attendee_setup` yourself (it creates your own schema), then follow the attendee guide for one scenario.
5. Fill in the placeholders in `docs/attendee-guide.md` (workspace URL, catalog, warehouses, notebook path) and share it with attendees.

> The data isn't included. Use **fictional** retailers, suppliers and brands only.
