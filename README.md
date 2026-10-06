# L.E.D.G.E.R.
**Language-Enabled Data Governance & Expense Resolution**

> A secure, evidence-backed natural-language interface for authorised expense and budget data.
> Most AI finance tools ask you to trust the answer. LEDGER lets you verify it.

---

## Why LEDGER

| Typical AI finance chatbot | LEDGER |
|---|---|
| A language model calculates numbers and can hallucinate arithmetic | Questions are turned into a validated query. Code does all the math |
| Returns a bare number | Returns the number, formula, filters and source transactions |
| Access control lives in the prompt and can be bypassed | Scope is enforced server-side. A prompt cannot override it |
| Guesses on vague or unsupported questions | Asks for clarification or refuses safely (for example, forecasts) |
| No record of what happened | Every query is audited: who, what, which rows, what result |
| "It works" is a claim | A benchmark suite measures it |

## How it works

```
User → UI → Authentication → RBAC (trusted scope)
     → Query Compiler (validated structured query)
     → Authorized data access (SQLite)
     → Deterministic calculation (Python/SQL)
     → Audit log → Answer + source rows → UI
```

**Core rules**
1. Financial numbers are only ever produced by the calculation engine, never by the query compiler.
2. User scope comes from the authenticated session, never from the frontend or the prompt.
3. Every executed answer is based on real records and exposes its source rows.
4. Missing, ambiguous or out-of-scope requests are clarified or refused, never guessed.
5. The MVP uses INR only. There is no FX conversion, ERP connector, receipt OCR or forecasting.

## Supported queries

`sum_expenses` · `category_breakdown` · `top_transactions` · `count_expenses` · `remaining_budget` · `source_lookup`

The calculation engine also supports `burn_rate` (spend ÷ budget × 100).

Example:

```
"How much did I spend on food in September 2026?"
→ { "intent": "sum_expenses", "category": "Food",
    "date_range_start": "2026-09-01", "date_range_end": "2026-09-30" }
→ Result + formula + filters + source row IDs
```

## Tech stack

Python · React + TypeScript · pandas · SQLite · Pydantic v2 · Plotly · pytest · FastAPI (query compiler API boundary)

## Project structure

```
L.E.D.G.E.R/
├── auth/          Authentication, session, RBAC           (Shubham)
├── calculation/   Deterministic calculation engine         (Shaurya)
├── query/         Query compiler, Pydantic schemas         (Niketan)
├── database/      SQLite connection, models, ingestion     (Divyapunj)
├── frontend/      UI                                       (Akanksha)
├── audit/         Audit logger and retrieval               (Harshit)
├── tests/         pytest suite and benchmark data          (Harshit)
├── data/          Sample CSVs (expenses, budgets, users)
├── app.py         Backend integration boundary
├── INTEGRATION_CONTRACT.md
├── requirements.txt
└── .env.example
```

## Getting started

```bash
git clone https://github.com/coder6e43/L.E.D.G.E.R.git
cd L.E.D.G.E.R

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # never commit .env
```

**Load the sample data** (creates `data/ledger.db`):

```bash
python -m database.ingestion
```

To reset, delete `data/ledger.db` and run the command again.

**Run the app:** `TODO: add the final command, for example streamlit run frontend/app.py`

## Sample data

| File | Contents |
|---|---|
| `data/sample_expenses.csv` | Expense rows (INR) across several cost centres and months, with a few deliberately invalid rows |
| `data/sample_budgets.csv` | Monthly budgets per cost centre and category |
| `data/sample_users.csv` | Demo users with roles and cost centres (passwords are stored as bcrypt hashes) |

Allowed categories: Food, Travel, Software, Office Supplies, Utilities, Marketing, Training, Miscellaneous.

The sample file includes deliberately bad rows (a duplicate ID, an invalid category and an impossible date). Ingestion must reject them visibly.

## Security model

- **Authentication** verifies the user. Passwords are hashed with bcrypt.
- **RBAC** derives the user's trusted scope from their role (Employee: own records; Manager: own cost centre; Admin: organisation).
- The calculation engine filters every SQL statement by the authorised cost centre. It uses parameterised SQL only, never string interpolation.
- If a query's `user_scope` conflicts with the authorised scope, the request is rejected.
- Query requests do not accept authorisation fields from the client.
- The audit log never stores passwords or hashes.

## Audit trail

Each processed query is stored in the `query_audit` SQLite table:

`query_id` · `timestamp` · `user_id` · `scope` · `raw_prompt` · `parsed_json` · `applied_filters` · `source_row_ids` · `numeric_result` · `execution_status` · `latency_ms`

Statuses: `SUCCESS`, `REFUSED`, `CLARIFY`, `ACCESS_DENIED`.

A logged result can be traced to its source: numeric result → `source_row_ids` → exact database rows.

```python
from audit.logger import get_recent
get_recent(limit=20)
```

## Testing

```bash
python -m pytest -q
```

The suite includes:
- audit logger and security tests
- an independent pandas ground truth (test-only) that the calculation engine is verified against
- engine tests covering sums, counts, top-N, source rows, budgets, burn rate, cost-centre isolation, mixed currency and invalid input
- a 40-scenario benchmark: totals, date ranges, category synonyms, remaining budget, source-row audit, ambiguous prompts, unsupported or future requests, and cross-user access

Targets: 100% calculation accuracy · 0% unauthorised leakage · 100% source-row coverage · at least 95% safe-refusal precision.

## Team

| Module | Owner | Branch |
|---|---|---|
| Authentication + RBAC | Shubham | `feature/auth-rbac` |
| Calculation engine | Shaurya | `feature/calculation-engine` |
| Query compiler | Niketan | `feature/query-compiler` |
| Database + ingestion | Divyapunj | `feature/database-ingestion` |
| Frontend + UI/UX | Akanksha | `feature/frontend` |
| Audit + testing | Harshit | `feature/audit-testing` |

## Contributing

1. `git checkout main && git pull origin main`
2. Create or switch to your feature branch.
3. Work only in your module. Coordinate before changing `app.py`, `requirements.txt`, `README.md` or `INTEGRATION_CONTRACT.md`.
4. Use meaningful commit messages and run `python -m pytest` before opening a PR.
5. Open a Pull Request into `main`. Never push feature work directly to `main`, and never commit `.env` or API keys.

See `INTEGRATION_CONTRACT.md` for the data each module hands to the next.

## Current status and limitations

- **MVP scope:** INR only, structured CSV data, no forecasting, no ERP integration.
- **Query understanding:** the compiler covers the supported intents listed above. Wording outside them is clarified or refused rather than guessed, and phrasing coverage will widen over time.
- **TODO:** update this section when the modules are merged. Items to track: the end-to-end pipeline entry point, audit coverage of compiler CLARIFY/REFUSED outcomes, and the frontend.

## Roadmap

Broader natural-language coverage · ERP connectors · multi-currency handling · forecasting with clearly stated uncertainty · richer budget-vs-actual dashboards.
