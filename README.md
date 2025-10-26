# TrustCheck — A Simple, Explainable Risk Checker for Elderly-targeted Health Products

> **Goal**: Input a product ID → aggregate evidence → output a transparent risk report.  
> **Context**: In China, aggressive marketing of “miracle” therapy/health products targets elderly people. Families struggle to judge credibility. This project turns that real problem into an explainable software plan with a runnable prototype.

---

## 1) Problem & Context (why this matters)
- Many products are exaggerated or misleading; some are overpriced “vitamins”, others lack proper health certificates.  
- Family story: my grandparents (well educated, high pensions) still buy such products. My father asked: *“Can we quickly check if a product is credible and compliant?”*  
- Root causes (5 Whys):
1. Why did people pay the 'IQ tax'? → Lack of authoritative, aggregated product informationand warnings.​
2. Why lack of such info? → Information are across official notices, media, reviews.​
3. Why is aggregation hard? → Data formatsdiffer, reliability varies, product IDs are notstandardized.​
4. Why can't users search easily? → No simpletool: 'input product ID → get a report'.​
5. Why hasn’t anyone done it? → Legalauthority is hard to ensure, but technically, anevidence aggregation and risk scoring tool is feasible.
---

## 2) What a Program Can (and Cannot) Solve
**Solvable by software**
- Aggregate information from multiple sources, normalize fields, and present a one-page report.  
- Compute an **explainable** risk score (transparent rules & weights).  
- Produce a shareable HTML report with evidence links and audit trail.

**Not solved by software**
- Legal determination or enforcement. The tool **assists decisions**; authority remains with regulators/courts.

---

## 3) How Programming Changes the Original Process & Operating Model
**Original**: decisions based on ads/hearsay → high risk of overpaying or unsafe products.  
**With the program**:  
1) Enter product ID → 2) aggregate evidence → 3) see scores/flags/links → 4) discuss a **traceable**, explainable result.  
**Operating model change**: From impulse to **evidence-first** decisions (a quick, repeatable pre-purchase step).

---

## 4) Requirements on the Program
**Functional**
- Input product ID (and name/brand search).  
- Aggregate: official notices, category, consumer reviews.  
- Compute Authority/Consumer/Combined scores + Risk flags.  
- Output terminal summary and **one-page HTML** report with score breakdown & links.

**Non-functional**
- **Explainability** (rule breakdown & tunable weights), **Traceability** (source links & audit),  
- **Robustness** (not-found / insufficient info paths), **Usability** (elder-friendly UI).

---

## 5) Usage Scenarios & Runtime Requirements
- Elderly consumers checking before purchase.  

**Runtime (demo)**: local is sufficient.  
**Runtime (full design)**: small web server + background data jobs; works on phone/tablet/PC browsers.

---

## 6) Planned Software Architecture 
![Architecture](./architecture.png)

**A. Interfaces (elder-friendly, HTML)**
- **Public Web Pages:**  
  1) **Home / Search** — one large input box for *Product ID*, big “Search” button.  
     - “No ID found?” expandable help: where to find IDs; warning that lack of ID is a risk signal.  
     - Language toggle (zh/EN), very large font, high contrast, keyboard focus states, ARIA labels.  
  2) **Report Page** — clear sections: Headline score, Risk flags (red/amber/green),  
     Score breakdown (why), Evidence links (official/reviews), Last updated time.  
  3) **Print/Share** — printer-friendly CSS; “Save as PDF” button (native browser print).  
- **Accessibility & Elder-friendly design:** ≥18–20px base font, high color contrast, large hit areas, plain words, no clutter.

**B. Application/API Layer**
- **Endpoints**  
  - `GET /api/products/:id` → normalized product + latest scores + flags + evidence list.  
  - `GET /api/search?q=` → fuzzy matches (name/brand/alias).  
  - `POST /api/feedback` (optional) → collect suspected products (lead only; no adjudication).  
- **Auth**: public read endpoints; rate limiting; admin endpoints protected.

**C. Scoring & Rules Engine (explainable, configurable)**
- Authority score (registration/cert/penalties with caps).  
- Consumer score (ratings × reviewer reputation × time-decay).  
- Combined score `T = wA*A + (1−wA)*C`, weights in config.  
- Rule-based flags: `ELDERLY_SENSITIVE`, `NO_AUTH_RECORD`, `PENALTY_HISTORY`,  
  `LOW_RECENT_RATING`, `EVIDENCE_CONFLICT`.  
- **Explainability API** returns *per-rule contributions*.

**D. Data & Ingestion**
- **Sources**: official notices, public black/white lists, curated review feeds.  
- **Ingestion jobs**: fetch → parse → map to canonical schema → validate → store.  
- **Canonical schema** (DB or files): `products`, `authorities`, `reviews`, `scores`, `audits`.  
- **CSV** remains as a **teaching simulator** for heterogeneous sources; later replaced by real APIs/DB.

**E. Storage**
- **Phase 1 (course)**: CSV files (for demo).  
- **Full design**:  
  - Relational DB (PostgreSQL/MySQL) for normalized tables.  
  - Object storage for cached HTML reports & evidence snapshots.  
  - Optional search index (e.g., SQLite FTS/Meilisearch) for fuzzy name/brand search.

**F. Audit & Observability**
- Append-only **audit log** for data updates & score versions.  
- **Health checks**, basic metrics (ingestion counts, errors, coverage).  
- Deterministic scoring (same inputs → same outputs) for verifiability.

**G. Deployment (lightweight)**
- Single small server (or container) serves HTML + API.  
- Nightly ingestion job (cron) updates sources and recomputes scores.  
- Static HTML reports are cacheable/printable for families.

---

## 7) Ensuring Correct Functioning (quality)
- **Schema validation** on records; fail fast on missing critical fields.  
- **Unit tests** for scoring (caps, time-decay monotonicity, boundaries).  
- **test cases** (e.g., `CN-MED-0004`) to assert end-to-end outputs.  
- **Assertions**: scores in [0..100], flags from known set; 404/“insufficient info” paths tested.  
- **Auditability**: scores carry timestamp + rule contributions.

---

## 8) Usability Considerations (elder-friendly)
- Large fonts, high contrast, single task per page (input → report), plain language.  
- “No ID found?” inline help; print/PDF support; minimal scrolling; keyboard and screen-reader friendly.  
- Report layout: **Headline decision** → **Why** → **Evidence links** (in that order).

---

## 9) How to Use

### A) CLI demo
python app.py CN-MED-0004
# Output: terminal summary + report_CN-MED-0004.html
### B) For real elderly users (final product flow)

1.Open the Home page (large single input).

2.Enter the Product ID from package/invoice; click Search.

3.Read the Report page: headline score & red/amber/green flag, short reasons, official links.

4.Click Print to get a PDF and discuss with family.

5.If no ID is visible, open “No ID found?” help — treat as a risk signal; consider not buying or ask a trusted pharmacist/doctor.

## 10) Future Work (from prototype to full system)

Replace CSV with official/regulatory APIs and curated databases.

Add fuzzy search and name/brand aliasing for non-ID use.

Digital signatures & timestamps on reports; offline print packs for community centers.

Multilingual content (zh/EN), accessibility audits, and nurse/pharmacist review workflows.

