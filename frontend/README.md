# ALTcredit frontend (Vite + React)

Implements the Stitch wireframes in `Artifacts/stitch_remix_of_altcredit_alternative_credit_scoring`.

## Run

```bash
# terminal 1 – API and bank (from backend/, venv activated)
uvicorn app.main:app --port 8000
uvicorn bank_mock.main:app --port 8001     # needed for the Apply flow
# terminal 2 – UI (from frontend/)
npm install && npm run dev                 # http://localhost:5173, /api is proxied to :8000
npm run build                              # production bundle in dist/
```

Demo logins use the "Demo preset" button on the sign-in page (`USR_002`, or lender `primebank`).

## Pages

| Route | Page |
|---|---|
| `/` | Landing page (scroll-reveal animations) |
| `/login`, `/signup`, `/lender/signup` | Sign in; four-step borrower sign-up; lender sign-up |
| `/dashboard` | Score, pillar breakdown, explanation, statement upload, lender-visibility consent |
| `/simulator` | What-if simulator |
| `/recommendations` | Product matches, lender offers, "how to qualify" plans |
| `/bank/:productId` | Partner-bank hand-off: redirect → review → processing → result |
| `/lender` | Lender portal: anonymised candidate search, bulk offers |

## Notes

- **Theming** — colours are CSS variables in `src/styles.css`. `data-theme="light|dark"` on `<html>`
  is set before first paint by a small script in `index.html`; `components/ThemeToggle.jsx` flips it
  and stores the choice in `localStorage`.
- **Motion** — CSS keyframes in `styles.css` (app) and `pages/landing.css`; `CountUp` in
  `components/ui.jsx` animates numbers. All of it respects `prefers-reduced-motion`.
- **Bank pages** — `src/banks.js` defines the three fictional banks and the product→bank mapping;
  `pages/Bank.jsx` + `bank.css` render them. They are always light and independent of the app theme.
- **Sign-up** — in `pages/Signup.jsx`, money-habit answers are choice bands with an "I don't know"
  option, and attaching a CSV removes the required fields after the account step.
- Wireframe elements the backend has no data for (provider names, "% match", capital-pool allocation,
  employment personas, tenure) are intentionally not shown rather than invented.
