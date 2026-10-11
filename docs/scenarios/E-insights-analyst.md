# Scenario E: Insights Analyst

**Theme:** Perfect Store Command Centre: from sell-out to shelf · **Team:** 05 · **Schema:** `team_05`

> **Your persona:** *Aisha is the agency's insights analyst. Merchandisers write thousands of visit notes every month ("shelf empty",
> "display damaged", "price tag missing"), but nobody reads them. She wants to turn those notes into structured insight and link it
> to OSA and sales.*

Follow the sprint steps in the [attendee guide](../attendee-guide.md). This document tells you **what to build** for your persona.
Your team uses **AI Functions** from the start (not just in Sprint 5).

---

## Business questions to answer

1. What are the **most common issues** merchandisers report, and are they growing?
2. Where (region, retailer, store) are issues **concentrated**?
3. Do stores with more **out-of-stock notes** have lower OSA and lower sales?
4. What is the **sentiment** of the notes, and does it differ by region or retailer?

## Data to focus on

`visit_notes`, `fact_store_visits`, `dim_store`, `dim_merchandiser`, `fact_sales_weekly`, `dim_date`

---

## Sprint 1: Dashboard v1 (quick win), plus the AI enrichment step

1. **First, enrich the notes** with AI Functions and save the result in your schema, for example:
   ```sql
   CREATE OR REPLACE TABLE team_05.visit_notes_enriched AS
   SELECT *,
          ai_classify(note_text, ARRAY('out of stock', 'damaged display', 'missing price tag',
                                       'planogram issue', 'competitor activity', 'other')) AS issue_type,
          ai_analyze_sentiment(note_text) AS sentiment
   FROM team_05.visit_notes;
   ```
   > Try it on `LIMIT 100` first, then run it on all the rows. Column names are examples, so check them in Catalog Explorer.
2. Suggested visuals (pick 4–6):
   - KPI counters: notes, % of notes that are negative, % out-of-stock
   - Issue type by week (stacked bar)
   - Issues by region / retailer (heatmap or bar)
   - Sample of the latest negative notes (table)
   - Filters: Issue type, Region, Retailer, Week range

## Sprint 2: Metric views

| Metric view | Must-have measures | Stretch measures |
|---|---|---|
| `mv_notes` (on `visit_notes_enriched`) | Notes, Negative notes %, Out-of-stock notes % | Issues per 100 visits |
| `mv_execution` | Visits, Avg OSA % | % of stores below the OSA target |

Then rebuild the dashboard on the metric views and add an **"out-of-stock notes vs OSA % by region"** visual.

## Sprint 3: Genie test questions (ask them exactly as written)

1. How many visit notes were written last month?
2. What are the top 5 issue types?
3. Which region reports the most out-of-stock issues?
4. What percentage of notes are negative this quarter?
5. Show out-of-stock notes by week for the last 3 months.
6. Which retailer has the most damaged display notes?
7. Do stores with out-of-stock notes have lower OSA?
8. Which merchandisers write the most notes per visit?
9. List the 10 stores with the most negative notes.
10. Is competitor activity increasing?

## Sprint 4a: Describe these first

`visit_notes_enriched` (especially `issue_type`, `sentiment`, `note_text`), `visit_notes`, `fact_store_visits`, `dim_store`

## Sprint 4b: Genie tuning hints

- Instructions: what the **issue types** mean, that "negative" means sentiment = negative, the **OSA target (85%)**, and the **fiscal calendar**.
- SQL expressions: the filter `Out-of-stock notes` and the measure `Issues per 100 visits`.
- Example SQL: joining notes to visits and OSA by store and week.

## Sprint 5 ideas

- **AI Functions (stretch):** use `ai_query` to write a weekly summary of the notes for each region, and show it on the dashboard.
- **App:** Tab 1 is a searchable table of the enriched notes, and Tab 2 has issue trend and region visuals.

## Demo tip

Turn text into action: "Out-of-stock notes are up X% in Region Y, and OSA is down there. Here is the AI-written summary for the field team."
