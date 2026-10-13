# Databricks AI/BI Hackathon: Perfect Store Command Centre

A ready-to-run **4-hour hackathon** on Databricks covering **AI/BI Dashboards, Unity Catalog Metric Views, data descriptions, Genie**
and **Databricks Apps built with Genie Code**.

> *You are the insights team at a fictional retail-execution agency. Your FMCG clients ask every Monday: how did we sell last week,
> did we hit budget, and what is happening on the shelf? Build the command centre that answers these questions.*

## Approach: quick win first, then make it better

| Area | Quick win | Improve | See the difference |
|---|---|---|---|
| Dashboards | Dashboard v1 straight on the tables | Rebuild on **metric views** | Same KPIs everywhere, less SQL |
| Genie | Genie space on undocumented tables | **Describe the data** in Unity Catalog, then add instructions, sample questions, SQL expressions, metric views | Re-ask the same questions and compare |
| App | Tab 1: data table | Tab 2: visuals | Built with Genie Code |

## Data model

One catalog, one **read-only source schema** (`hack_14oct`), and **one schema per attendee**, which they create themselves. Each attendee **copies** the source
tables into their own schema, so they own the data **and its descriptions**.

## Repository layout

```
attendees/                     # everything attendees need (share this folder)
├── attendee-guide.md          # step-by-step guide: business questions, sprints, Genie questions, troubleshooting, cheat-sheets, app prompts, bonus custom visual
└── 01_attendee_setup.py       # every attendee runs this first: create their own schema, then deep clone every table from hack_14oct
docs/
└── hackathon-plan.md          # facilitator plan: agenda, data strategy, metric views, Genie ladder, grants, risks
hack_setup/                    # facilitator only: everything to set up the hackathon
├── 00_facilitator_runbook.py  # step-by-step setup and test: schema, synthetic data as Delta tables in hack_14oct, constraints, grants, testing
└── 02_generate_synthetic_data.py  # synthetic, fictional dataset generator (called from runbook Step 3)
```

## Getting started (facilitator)

1. Clone this repo into your Databricks workspace as a Git folder (or import the `attendees/`, `docs/` and `hack_setup/` folders).
2. Open `hack_setup/00_facilitator_runbook`, set the `catalog` widget (the source schema defaults to `hack_14oct`), and run it **step by step**.
3. Step 3 generates the synthetic dataset as Delta tables in `hack_14oct`. Make that schema read-only for participants.
4. Test as an attendee (runbook Step 6): run `attendees/01_attendee_setup` yourself (it creates your own schema), then follow the attendee guide.
5. Fill in the placeholders in `attendees/attendee-guide.md` (workspace URL, catalog, warehouse ID) and share the `attendees/` folder with attendees.

> No data files are included: the runbook generates a fully synthetic, fictional dataset.
