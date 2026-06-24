# AI Website Builder Competitive Intelligence Pipeline

Internal tooling to collect, monitor, and report on competitors in the AI Website Builder space—turning public website data into structured intelligence and HTML deliverables.

---

## Problem

Competitive analysis in fast-moving SaaS categories is usually manual: open five homepages, copy pricing into a spreadsheet, paste feature lists into slides, repeat next month.

That approach breaks down quickly:

- **Stale data** — spreadsheets diverge from live product pages within weeks
- **No diff history** — teams notice pricing changes late, often after a launch cycle
- **Unstructured output** — raw notes don't scale into comparison matrices or strategic summaries
- **High maintenance cost** — each new competitor requires bespoke research

This project automates the repeatable parts of that workflow for the AI Website Builder segment (Lovable, Bolt, v0, Replit, Durable) while keeping human review in the loop for quality and interpretation.

---

## Solution


| Capability                | Implementation                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------- |
| **Automatic collection**  | `collect_competitors.py` scrapes configured competitor sites and writes normalized JSON |
| **Structured analysis**   | Fixed schema: pricing, target customer, core features, technical highlights             |
| **HTML report**           | `generate_report.py` renders comparison tables and narrative sections                   |
| **Competitor monitoring** | `monitor.py` saves dated snapshots and diffs the latest two runs                        |
| **Strategic insights**    | `strategic_insights.py` applies rule-based synthesis (no external LLM)                  |


Collection and reporting are decoupled. Monitoring runs automatically after each collection. Insights and Builder's Perspective are report-layer additions that don't require re-scraping.

---

## Architecture

```
Competitor Websites
        ↓
    Collector          (scripts/collect_competitors.py)
        ↓
  competitors.json     (data/competitors.json)
        ↓
Monitoring Pipeline    (scripts/monitor.py → history/, change_report.json)
        ↓
Strategic Insights Engine  (scripts/strategic_insights.py)
        ↓
    HTML Report          (scripts/generate_report.py → reports/report.html)
```

**Data layout**

```
.
├── data/
│   ├── competitors_config.json   # competitor registry (extensible)
│   ├── competitors.json          # latest collection output
│   ├── change_report.json        # diff vs previous snapshot
│   └── history/YYYY-MM-DD.json   # dated snapshots
├── scripts/
│   ├── collect_competitors.py
│   ├── monitor.py
│   ├── strategic_insights.py
│   └── generate_report.py
└── reports/report.html
```

Competitor list lives in config, not in Python. New competitors are added by editing JSON.

---

## Key Features

**Config-Driven Competitors**  
`data/competitors_config.json` defines name, website, optional `pricing_url`, and optional `overrides` for manual correction. No script changes required to add a competitor.

**Fault Tolerance**  
Each competitor is collected in an isolated try/except block. One failed scrape does not abort the batch. Failures log to stderr and emit empty-field records.

**Monitoring Pipeline**  
Every collection run saves `data/history/YYYY-MM-DD.json`, compares the two most recent snapshots, writes `data/change_report.json`, and prints `[CHANGED]` / `[UNCHANGED]` lines to the terminal. Skipped when fewer than two snapshots exist.

**Strategic Insights**  
Rule engine derives market opportunities, entry recommendation, top risks, and future monitoring metrics from collected data. Reproducible, no API dependency.

**Builder's Perspective**  
Fixed narrative section (report layer only) on the shift from *Build Website* to *Grow Website*—complementing data-driven insights with a structured viewpoint.

---

## Future Monitoring Metrics

The pipeline tracks these dimensions over time:


| Metric                     | Why it matters                                                                         |
| -------------------------- | -------------------------------------------------------------------------------------- |
| **Pricing Changes**        | Tier structure and credit models signal monetization strategy and competitive pressure |
| **New Features**           | Feature velocity indicates where incumbents are investing R&D                          |
| **Positioning Changes**    | Hero messaging shifts reveal target segment pivots                                     |
| **Integrations**           | Third-party connections (CRM, payments, hosting) define product boundary and lock-in   |
| **Target Customer Shifts** | Movement toward Enterprise, SMB, or developers changes competitive overlap             |
| **Landing Page Messaging** | CTA and value-prop ordering reflect GTM priority                                       |


Current implementation diffs four fields per run: `pricing`, `core_features`, `target_customer`, `technical_highlights`. The metrics above guide what to watch manually and what to automate next.

---

## Example Output

`**data/competitors.json`** — machine-readable source of truth for downstream report generation and diffs.

```json
{
  "name": "v0",
  "website": "https://v0.dev",
  "pricing": "Free | $5 of included monthly credits | Team ...",
  "target_customer": "Your collaborative AI assistant to design, iterate, and scale full-stack applications.",
  "core_features": ["Templates", "Deploy to Vercel", "Integrate with apps"],
  "technical_highlights": ["Vercel", "Github", "Full-Stack", "Deploy"]
}
```

`**reports/report.html**` — stakeholder-facing deliverable: overview cards, feature/pricing/customer matrices, Strategic Insights, Builder's Perspective.

`**data/change_report.json**` — structured diff between the last two snapshots; feeds alerting or review workflows.

```json
{
  "previous_snapshot": "YYYY-MM-DD",
  "current_snapshot": "YYYY-MM-DD",
  "competitors": [
    { "name": "Lovable", "status": "changed", "changes": ["pricing"] },
    { "name": "Bolt", "status": "unchanged" }
  ]
}
```

---

## Running Locally

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -r requirements.txt

python scripts/collect_competitors.py   # collect + snapshot + diff
python scripts/generate_report.py       # render report.html
```

Outputs:

- `data/competitors.json`
- `data/history/YYYY-MM-DD.json`
- `data/change_report.json` (when ≥2 snapshots exist)
- `reports/report.html`

---

## Estimated Engineering Effort

Per `ai-log.md`, assuming a developer familiar with Python and including local testing:


| Phase                 | Hours       |
| --------------------- | ----------- |
| Project Scaffolding   | 1.5 – 2     |
| Competitor Collection | 2 – 2.5     |
| Monitoring Pipeline   | 1 – 1.5     |
| Strategic Analysis    | 1.5 – 2     |
| Report Generation     | 1 – 1.5     |
| **Total**             | **7 – 9.5** |


Upper bound ~10 h with data-quality review cycles (e.g. filtering nav noise from `core_features`).

---

## Builder Observation

Most competitors focus on helping users create websites faster.

However, website creation is increasingly becoming a commodity capability.

The larger opportunity may exist after launch:

- SEO
- Lead generation
- Conversion optimization
- Customer acquisition
- Business growth workflows

In other words, the market may gradually shift from:

Build Website

to

Grow Website

This project currently monitors website builders, but the same pipeline could be extended to track the emerging Website Growth Agent category.

---

## Data Quality Notes

- Collection uses static HTML scraping (`requests` + BeautifulSoup); no JavaScript is executed.
- Content injected by the browser after hydration is not captured.
- Lovable and Replit use site-specific heading/keyword extractors to supplement the generic `<li>` pipeline.
- v0 features are mapped directly from SSR `<h2>`/`<h3>` headings, which are fully present in the initial response.
- Pricing is heuristic-based (regex on tier words and price tokens) and is not structured into comparable tiers.
- Feature quality varies by competitor: Durable and v0 are strongest; Lovable and Replit required targeted fixes.

---

## Future Work


| Item                         | Status                 | Rationale for deferral                                                                                                                                                                                                                                                                                                                                                                      |
| ---------------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Per-site Parser**          | Not implemented        | Generic heuristics validated the pipeline first; site-specific parsers improve accuracy but increase maintenance per competitor                                                                                                                                                                                                                                                             |
| **Scheduled Monitoring**     | Not implemented        | Requires cron/CI and stable hosting; manual runs sufficient for current scope                                                                                                                                                                                                                                                                                                               |
| **Notification Integration** | Not implemented        | Depends on scheduled runs and defined alert thresholds; `change_report.json` is the interim interface                                                                                                                                                                                                                                                                                       |
| **LLM-assisted Analysis**    | Deferred intentionally | During development, data quality issues (navigation noise, persona-feature misclassification, marketing copy contamination) were identified in the collection layer. Instead of adding an LLM on top of noisy inputs, the project prioritizes improving extraction fidelity first. The decision was to delay AI-generated insights until the underlying data becomes sufficiently reliable. |


See `ai-log.md` for AI-assisted development process, known extraction errors, and human decision log.