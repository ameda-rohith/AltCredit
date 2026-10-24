# AltCredit

**Alternative credit scoring for people with thin credit files.**

AltCredit scores users on 15 behavioural, lifestyle and repayment features instead of a
traditional bureau history — via a transparent, rule-based engine (no black-box ML) — and turns
that score into something actionable: a factor-by-factor explanation, a "what-if" simulator, a
counterfactual planner ("what do I need to change to qualify for product X"), live product
matching with a mock partner-bank hand-off, and an anonymised marketplace where lenders can find
and make offers to qualifying users without seeing their identity until they accept.

It's a full-stack prototype: a FastAPI + SQLite backend, a separate mock partner-bank API, and a
Vite + React frontend.

## Why

Traditional credit scoring locks out people with no/thin credit history even when their
underlying financial behaviour (steady employment, on-time rent, healthy spend-to-income ratio,
low volatility) is solid. AltCredit approximates a bureau-style score from that behavioural data
so those users become visible to lenders, while keeping every point of the score explainable —
each factor, its weight, and why it scored the way it did are always inspectable, unlike a
trained model.

## How it works

1. **Score** — 15 features (employment stability, housing, digital footprint, education,
   spend-to-income, expense diversity, cash-flow volatility, savings buffer, on-time payment rate,
   debt-to-income, credit utilisation, delinquency, positive habits, risk flags) feed a tiered
   rule engine across 3 pillars — **Lifestyle** (max 350), **Spending Behaviour** (max 350),
   **Repayment Discipline** (max 570) — plus ±50 adjustments, summed and capped to a **0–1000**
   score.
2. **Explain** — every factor is bucketed into positive / negative / weak contributors with a
   plain-language sentence, plus the top 5 drivers and improvement suggestions.
3. **Simulate & plan** — the what-if simulator re-scores a user with hypothetical changes; the
   target planner works backwards from a product's minimum score to the smallest set of feature
   changes that would qualify.
4. **Match & apply** — the score is checked against a small product catalog (Starter Card 350 /
   Micro-Loan Lite 550 / Standard Card 650 / Premium Loan 750). "Apply" redirects the user to a
   partner-bank page (one of three fictional banks, each with its own look) and, on submit, calls a
   separate mock bank API that checks the score against the product minimum before approving.
5. **Lender marketplace** — lenders search and filter an **anonymised** pool of leads (score,
   tier, PD, income, DTI only — no name/email), and push offers in bulk. A user's identity is
   revealed to a lender only after that user explicitly accepts their offer.

Probability of default is derived directly from the score (`PD = 1 − score/1000`) rather than
trained, since the underlying dataset carries no default labels — see [Assumptions &
limitations](#assumptions--limitations).

## Frontend highlights

- **Light and dark themes** — a neumorphic "soft UI" light theme and a charcoal-and-emerald dark
  theme, switchable from every page. The choice is remembered; first visit follows the OS setting.
- **Motion throughout** — page and card entrances, count-up scores, gauges and bars that draw in,
  scroll reveals on the landing page. Everything is disabled under `prefers-reduced-motion`.
- **Forgiving sign-up** — a four-step form where money-habit questions are plain-language choices
  (not raw percentages) with an "I don't know" option, and attaching a bank-statement CSV makes
  every question after the account step optional ("Skip the rest & get scored").
- **Partner-bank hand-off** — applying redirects to a bank-branded page (Sentinel State Bank,
  Pinnacle Bank or Rosewood Bank): review, consent, processing, then the pre-approval result. The
  banks are fictional and the pages are clearly labelled as a simulation.

## Project layout

```
AltCredit/
├── backend/               FastAPI API + SQLite (embedded, auto-seeded)
│   ├── app/               routes, ORM models, request schemas
│   ├── core/               settings, DB engine, password hashing
│   ├── services/           rule engine, scoring, what-if, target planner,
│   │                       explainability, product matching, PDF/JSON export
│   ├── bank_mock/          separate mock partner-bank FastAPI app (X-API-Key)
│   ├── data/               seed data (500 synthetic users)
│   ├── tests/               pytest suite (scoring, API, lender)
│   └── docs/BACKEND_GUIDE.md   full module-by-module walkthrough with diagrams
├── frontend/              Vite + React 19 UI (landing, sign-up, dashboard, simulator,
│   └── src/                 recommendations, partner-bank pages, lender portal)
├── machine_learning/      source data, cleaning notebook, product catalog
│   └── data/                 (still read by the backend at runtime)
└── Artifacts/             use-case doc, ER diagram, wireframes/design files
```

## Tech stack

| Layer | Stack |
|---|---|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.0, SQLite, Pydantic v2, ReportLab (PDF), pytest |
| Frontend | React 19, React Router 7, Vite 8 (plain CSS, no UI library) |
| Mock partner bank | A second, independent FastAPI app, API-key protected |

## Getting started

Requires Python 3.13+ and Node 18+.

```bash
# 1. Backend API (terminal 1)
cd backend
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                                # optional — see below
.venv/bin/uvicorn app.main:app --port 8000           # -> http://localhost:8000/docs

# 2. Mock partner bank (terminal 2) — needed for the "Apply" flow
cd backend
.venv/bin/uvicorn bank_mock.main:app --port 8001

# 3. Frontend (terminal 3)
cd frontend
npm install
npm run dev                                          # -> http://localhost:5173 (proxies /api to :8000)
```

Tip: run `source .venv/bin/activate` once per terminal to use plain `uvicorn …` instead of
`.venv/bin/uvicorn …`. The `/explain` endpoint answers 503 unless `OLLAMA_API_KEY` is set in
`backend/.env`; everything else works without it.

The source datasets in `machine_learning/data/` are not tracked in git (they are git-ignored; only
`product_catalog.json` is). The backend and its tests read them at runtime, so a fresh clone needs
those files copied into that folder before the API will start.

The first backend start creates `backend/altcredit.db` and auto-seeds 500 synthetic users (from
`backend/data/merged_data.json`) and 3 demo lenders. Seeding is idempotent — later restarts leave
existing data alone.

**Demo logins** (password is `DEMO_PASSWORD`, default `altcredit-demo`):
- Users: `USR_001` … `USR_500` (or use the "Demo preset" button on the sign-in page — `USR_002`)
- Lenders: `primebank`, `microfin`, `neolend`

### Run the tests

```bash
cd backend
.venv/bin/python -m pytest -q
```

Covers the rule engine against ground-truth CSVs for all 500 seeded users, end-to-end API flows
(scoring, what-if, target planning, registration, CSV upload, bank apply), and the lender
marketplace (anonymity guarantees, offer lifecycle, identity reveal on accept).

## API overview

All routes are under `/api/v1`. Full endpoint reference and request/response shapes:
[`backend/README.md`](backend/README.md) · [`backend/docs/BACKEND_GUIDE.md`](backend/docs/BACKEND_GUIDE.md).

| Area | What it covers |
|---|---|
| `auth` | Login / registration (with full profile capture) returning a signed bearer token |
| `users/consent` | Opt in to / out of the lender candidate pool |
| `scoring` | Get score/explanation, update profile, upload transaction CSV, view history |
| `scoring/what-if` | Simulate profile changes without persisting them |
| `scoring/target` | Counterfactual plan to reach a product's minimum score |
| `scoring/report.pdf` / `export.json` | Transparency report / raw export |
| `dashboard` | One-call payload combining score, verdict, drivers, next steps, history |
| `products` | Catalog, live recommendations, apply (hands off to the mock bank), offers |
| `lender` | Anonymised candidate search & filtering, bulk offers, offer status |

Every route except `/health`, the product catalog and `/auth/*` needs an `Authorization: Bearer <token>`
header, and a token only opens its own account (see the backend README, **Auth**). Set `SECRET_KEY` in
`backend/.env` before sharing the API.

## Assumptions & limitations

- **PD is derived, not trained.** `PD = 1 − score/1000`. The source dataset has no default label,
  so no ML default-probability model is trained (`scikit-learn`/`numpy` are pinned but unused). The
  figure is a score-derived *risk indicator*; payloads carry `pd_basis: "score_derived"` and the UI,
  PDF and LLM prompt label it that way.
- **Missing data** is filled with conservative (zero-point) defaults and reported back as
  `missing_fields`; a thin file with no recorded credit lines scores as "clean" rather than
  penalised, since absence isn't evidence of risk.
- **Score cap**: pillar maxima sum to ~1320 but the score is clamped to 1000, so a `score_capped`
  flag surfaces when the cap is masking further what-if gains.
- **Prototype-grade auth** — signed bearer tokens and ownership checks, but demo accounts share one
  password, there is no refresh/revocation, and rate limiting is in-memory (single process).
- **Statements are self-reported.** An uploaded CSV is not verified against a bank, so it can raise a
  score; it can never lower a delinquency already on file.
- **Sign-up answers are approximate.** The plain-language choices map to representative values
  (e.g. "Almost always" → 90% on time), and anything marked "I don't know" is scored as missing.
- **Partner banks are fictional.** Sentinel State Bank, Pinnacle Bank and Rosewood Bank, their logos
  and copy are invented; only the general look of large retail banks is echoed. Which bank serves
  which product is a frontend mapping (`frontend/src/banks.js`).
- Names, emails and other identity fields for the 500 seeded users are synthetic.

## Documentation

- [`backend/README.md`](backend/README.md) — backend run instructions, layout, API table, assumptions
- [`backend/docs/BACKEND_GUIDE.md`](backend/docs/BACKEND_GUIDE.md) — full module-by-module walkthrough with sequence/ER diagrams
- [`frontend/README.md`](frontend/README.md) — frontend run instructions and page map
- [`Artifacts/`](Artifacts) — original use-case document, ER diagram, and design wireframes
