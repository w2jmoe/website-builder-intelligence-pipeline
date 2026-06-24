# Data Quality Audit — AI Website Builder Competitive Intelligence Pipeline

**Audit date:** 2026-06-24  
**Data source:** `data/competitors.json` (live scrape)  
**Collector:** `scripts/collect_competitors.py`

---

## 1. Current Scraping Methodology

### What `collect_competitors.py` actually does

| Component | Used? | Details |
|-----------|-------|---------|
| **requests** | Yes | `requests.Session.get()` fetches raw HTML (timeout 20s, custom User-Agent) |
| **BeautifulSoup** | Yes | Parses static HTML with `html.parser` |
| **JavaScript execution** | **No** | No Playwright, Selenium, Puppeteer, or headless browser |
| **API calls** | No | Does not call product JSON/API endpoints directly |

### Extraction pipeline (per competitor)

1. Fetch **homepage** + **pricing page** (`pricing_url` or `{website}/pricing`)
2. **target_customer** — `meta[name=description]` or `og:description`
3. **core_features** — first 8 valid `<li>` items + up to 6 `<h2|h3|h4>` headings matching `FEATURE_KEYWORDS`, merged and filtered
4. **pricing** — regex scan for `$€£` amounts and tier words (Free/Pro/Team/Enterprise) in `<span|p|div|h2|h3>`, joined with ` | `
5. **technical_highlights** — keyword presence scan across description + `<p|li|span>` for terms like React, Vercel, GitHub, Deploy, etc.

### Implication

The collector only sees **initial HTTP response HTML**. It does not wait for client-side rendering, hydration, or lazy-loaded sections. Any content injected purely via JavaScript after page load is invisible to the pipeline.

---

## 2. Per-Site Rendering Model Assessment

Live fetch analysis (status 200 for all sites, homepage + pricing):

| Site | HTML size (home) | Visible body text | Scripts | Next.js markers | Model | Rationale |
|------|------------------|-------------------|---------|-----------------|-------|-----------|
| **lovable.dev** | ~409 KB | ~2,046 chars | 129 | `_next/static` | **Hybrid** | Large SSR payload; feature copy in headings/sections; heavy JS hydration for interactive builder UI |
| **v0.dev** | ~1,038 KB | ~4,148 chars | 86 | `_next/static` | **Hybrid** | Vercel/Next SSR; feature headings present in initial HTML (`Prompt. Build. Publish.`, `Deploy to Vercel`, etc.) |
| **replit.com** | ~659 KB | ~9,762 chars | 126 | `__NEXT_DATA__`, `#root` | **Hybrid** | Substantial SSR text; nav `<li>` structure poor for feature extraction |
| **bolt.new** | ~101 KB | ~2,890 chars | 11 | `#root` (no Next) | **Hybrid / CSR-leaning** | Moderate static text; marketing headings in SSR; builder UI likely client-heavy |
| **durable.co** | ~752 KB | ~8,745 chars | 87 | `_next/static` | **Hybrid** | Rich SSR; product features embedded in `<li>` on homepage |

**None of these are pure CSR empty shells** — all return meaningful text in the first HTML response. However, **Lovable and Bolt have relatively low body-text-to-HTML ratios**, suggesting more content lives in JS bundles or structured data not surfaced as clean list items.

---

## 3. How Much Real Content Does the Current Logic Capture?

### Field-level capture estimate

| Competitor | target_customer | pricing | core_features | technical_highlights |
|------------|-----------------|---------|---------------|----------------------|
| Lovable | **High** (~85%) | **Medium** (~45%) | **Low** (~15%) | **Medium** (~50%) |
| v0 | **High** (~90%) | **Medium-High** (~60%) | **Medium-High** (~60%) | **High** (~75%) |
| Replit | **High** (~85%) | **Low** (~30%) | **Very Low** (~10%) | **Medium** (~55%) |
| Bolt | **High** (~85%) | **Medium** (~50%) | **Medium** (~40%, slogan-heavy) | **Medium** (~50%) |
| Durable | **High** (~90%) | **Medium** (~50%) | **High** (~70%) | **Low** (~20%) |

### Root causes of gaps

1. **DOM-order bias** — `<li>` traversal hits nav/footer/persona before product features (especially Lovable, v0 nav)
2. **Filtering side effects** — Persona/nav rules correctly remove noise but leave sparse feature sets (Lovable → 2 items)
3. **Heading keyword gate** — Features in headings without `FEATURE_KEYWORDS` are skipped (e.g. v0 `Sync with a repo`, `Agentic by default`)
4. **Pricing not structured** — Regex + pipe-join produces marketing fragments, not comparable tiers
5. **No JS** — Not the primary blocker for v0/Durable; **extraction heuristics** matter more than rendering for most gaps

### Raw HTML vs extracted (Lovable example)

Keywords **present in raw HTML** but **absent from core_features**:

`supabase`, `github`, `typescript`, `tailwind`, `collaborat`, `one-click`, `deploy`, `design system`, `chat`

→ `technical_highlights` captures React/Cloud/Deploy via keyword scan; **product capabilities are in the page but not mapped to features**.

---

## 4. Lovable — Detailed Gap Analysis

### Currently in `competitors.json`

```json
{
  "target_customer": "Build apps, websites, and digital products faster using Lovable's AI-powered platform, no deep coding skills required.",
  "pricing": "Enterprise | Teams from top companies build with Lovable | Product | Product Managers | Prototyping | Enterprise | Start for free... | Pro and Business subscriptions include grants for building and hosting with Cloud...",
  "core_features": ["Templates", "Discover templates"],
  "technical_highlights": ["React", "Cloud", "Deploy"]
}
```

### Public capabilities (from lovable.dev marketing / pricing, SSR-visible)

| Capability | On site | In JSON |
|------------|---------|---------|
| AI chat / vibe coding app builder | Yes | No |
| Websites + apps + digital products | Yes (target_customer only) | Partial |
| Templates library | Yes | Yes |
| Supabase integration (DB/auth) | Yes (in HTML) | No (not in features) |
| GitHub sync / export | Yes (in HTML) | No |
| Lovable Cloud hosting / deploy | Yes | Partial (Deploy in tech highlights) |
| React + TypeScript + Tailwind stack | Yes | Partial (React only) |
| Real-time collaboration / teams | Yes | No |
| Prototyping use case | Yes (in pricing noise) | No |
| Enterprise / security / SSO | Yes | No |
| Credit-based pricing (Free → Pro → Business) | Yes (pricing page) | Partial (unstructured) |

### Missing key capabilities

- AI prompt-to-app generation (core product)
- Supabase / database integration
- GitHub integration / code export
- One-click deploy / Lovable Cloud
- Team collaboration
- Structured pricing tiers (credits, monthly cost)

### Assessment

| Field | Sufficient for assignment? | Confidence |
|-------|---------------------------|------------|
| target_customer | Yes | High |
| pricing | Partial — has Free/Pro/Business signals but unreadable | Low-Medium |
| core_features | **No** — 2 template-related items vs ~10+ real capabilities | **Low** |
| technical_highlights | Partial — misses Supabase, GitHub, TypeScript, Tailwind | Medium |

---

## 5. v0 — Detailed Gap Analysis

### Currently in `competitors.json`

```json
{
  "target_customer": "Your collaborative AI assistant to design, iterate, and scale full-stack applications for the web.",
  "pricing": "Enterprise | v0 Pro | Prompt. Build. Publish. | ... | Free | $5 of included monthly credits | Team Popular | $30 of included monthly credits per user",
  "core_features": [
    "Templates", "Start with a template", "Prompt. Build. Publish.",
    "Integrate with apps", "Deploy to Vercel", "Edit with design mode", "Start with templates"
  ],
  "technical_highlights": ["Vercel", "Github", "Api", "Full-Stack", "Database", "Deploy"]
}
```

### Public capabilities (from v0.dev, SSR-visible in headings/HTML)

| Capability | On site | In JSON |
|------------|---------|---------|
| Prompt → Build → Publish workflow | Yes | Yes |
| Templates | Yes | Yes (with duplicates) |
| Deploy to Vercel | Yes | Yes |
| Integrate with apps | Yes | Yes |
| Design mode | Yes | Yes |
| Sync with GitHub repo | Yes (heading in HTML) | No |
| Create design systems | Yes (heading in HTML) | No |
| Agentic / multi-step AI | Yes (heading in HTML) | No |
| Mobile / create from phone | Yes (heading in HTML) | No |
| Figma-related workflow | Yes (in HTML) | No |
| Team plan + credit pricing | Yes | Partial ($5 / $30 captured) |
| Enterprise tier | Yes | Partial (in pricing string) |

### Missing key capabilities

- GitHub repo sync
- Design systems
- Agentic workflows
- Figma integration
- Mobile creation

### Assessment

| Field | Sufficient for assignment? | Confidence |
|-------|---------------------------|------------|
| target_customer | Yes | High |
| pricing | Partial — tier names + credit amounts present, not structured | Medium |
| core_features | **Mostly yes** — covers main workflow; gaps in sync/design-system/agentic | **Medium-High** |
| technical_highlights | Yes — strongest in dataset | High |

---

## 6. Other Competitors (Summary)

### Replit

- **Rendering:** Hybrid (Next.js, rich SSR text)
- **Captured:** Good target_customer; pricing sparse; **2 core_features** (`Design Freely`, `Build together`) — marketing slogans only
- **Missing:** Agent, Databases, Publish, Integrations, Mobile (visible in nav concatenation string but filtered out)
- **Verdict:** Insufficient core_features; acceptable target_customer

### Bolt

- **Rendering:** Hybrid / CSR-leaning
- **Captured:** 6 features, mostly hero copy + SEO/database mentions
- **Missing:** Structured pricing tiers; clean feature names (IDE, database providers, design system integration under marketing language)
- **Verdict:** Medium usability for comparison matrix

### Durable

- **Rendering:** Hybrid with excellent feature SSR in `<li>`
- **Captured:** 8 substantive features (AI Website Builder, SEO & GEO, templates, image/brand tools)
- **Missing:** Pricing structure ($0 free tier mentioned but not parsed); CRM/booking only implied
- **Verdict:** Best core_features in dataset; pricing still unstructured

---

## 7. Assignment Requirements — Sufficiency & Credibility

### Required fields (original assignment)

| Field | Dataset-wide verdict | Credibility (1–5) | Notes |
|-------|---------------------|-------------------|-------|
| **核心功能 (core_features)** | **Partially sufficient** | **2.5 / 5** | v0 & Durable usable; Lovable & Replit critically sparse; Bolt slogan-heavy |
| **定价 (pricing)** | **Partially sufficient** | **2 / 5** | Raw text exists for all; not comparable; Persona/nav noise in strings |
| **目标客户 (target_customer)** | **Sufficient** | **4.5 / 5** | All 5 competitors have accurate meta-description-level positioning |
| **技术特点 (technical_highlights)** | **Partially sufficient** | **3 / 5** | Keyword-based; misses stack details for Lovable; Durable under-reported |

### Can `competitors.json` support the deliverables?

| Deliverable | Supported? | Explanation |
|-------------|------------|-------------|
| HTML feature matrix | Yes, with caveats | Matrix renders but Lovable/Replit rows are misleadingly thin |
| Pricing comparison table | Weak | Table exists; analytical value low |
| Target customer comparison | Strong | Reliable across all competitors |
| Strategic Insights (rule engine) | Medium | Biased toward competitors with richer text (Durable, v0) |
| Monitoring diffs | Medium | Will detect scrape/filter changes as well as real product changes |

### Overall credibility assessment

**Moderate — suitable for a pipeline prototype, not for production competitive intelligence without remediation.**

**Strengths:**
- No fake/test data in current artifacts
- Config-driven, fault-tolerant architecture works
- target_customer consistently accurate
- v0 and Durable feature extraction demonstrates the approach can work on SSR-friendly pages

**Weaknesses:**
- Lovable core_features (2 items) do not represent the product; a reviewer comparing Lovable vs v0 will question data quality immediately
- pricing field is not analytically usable without post-processing
- No JavaScript execution limits capture on interactive builder UIs, but **heuristic extraction is the larger bottleneck** for Lovable/Replit even where SSR text exists

---

## 8. Recommendations (Documentation Only)

| Priority | Action | Expected impact |
|----------|--------|-----------------|
| P0 | Add `overrides` for Lovable (and Replit) core_features in `competitors_config.json` | Fixes thinnest matrix rows without architecture change |
| P1 | Lovable per-site parser targeting feature headings (`Meet Lovable`, product sections) | Captures AI builder, Supabase, GitHub from existing SSR HTML |
| P1 | Parse v0 headings without strict keyword gate, or expand `FEATURE_KEYWORDS` (`repo`, `figma`, `agentic`) | Recovers 4+ missing v0 features already in HTML |
| P2 | Structured pricing extraction (tier name + price + credits) | Makes pricing comparison credible |
| P3 | Playwright for pages where body-text/HTML ratio < 1% | Insurance for future CSR-heavy redesigns |

---

## Appendix: Live Fetch Metrics (2026-06-24)

| Site | Home HTML | Home body text | `<li>` count | Pricing page body text |
|------|-----------|----------------|--------------|------------------------|
| lovable.dev | 408,721 B | 2,046 chars | 57 | 5,744 chars |
| v0.dev | 1,038,408 B | 4,148 chars | 22 | 3,838 chars |
| replit.com | 659,486 B | 9,762 chars | 8 | 3,604 chars |
| bolt.new | 100,861 B | 2,890 chars | 25 | 3,523 chars |
| durable.co | 752,304 B | 8,745 chars | 18 | 5,312 chars |
