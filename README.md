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
attendees/                     # instructions only (share this folder with attendees)
└── 01_instructions.md         # the hackathon, sprint by sprint: business questions, Genie questions, hints, troubleshooting, app prompts, bonus custom visual
docs/
└── hackathon-plan.md          # facilitator plan: agenda, data strategy, metric views, Genie ladder, grants, risks
hack_setup/                    # facilitator only: everything to set up the hackathon
├── config.yaml                # settings: catalog, warehouse ID, attendee emails
├── 00_facilitator_runbook.py  # Run all: read-only hack_14oct with synthetic data, constraints, grants, one schema per attendee
└── 01_generate_synthetic_data.py  # synthetic, fictional dataset generator (called by the runbook)
```

## Getting started (facilitator)

1. Clone this repo into your Databricks workspace as a Git folder (or import the `attendees/`, `docs/` and `hack_setup/` folders).
2. In your workspace copy, fill in `hack_setup/config.yaml`: the catalog, the warehouse ID and the attendee emails.
   ⚠️ This repo is public, so don't commit real emails or IDs.
3. Open `hack_setup/00_facilitator_runbook` and click **Run all**. One execution reads `config.yaml`, builds the read-only `hack_14oct`
   with the synthetic data, grants access, and creates every attendee's schema (owned by them).
4. Test as an attendee: add yourself to `config.yaml` before the run, then follow `attendees/01_instructions.md` in your schema.
5. Fill in the placeholders in `attendees/01_instructions.md` (workspace URL, catalog, warehouse ID) and share the `attendees/` folder with attendees.

> No data files are included: the runbook generates a fully synthetic, fictional dataset.
