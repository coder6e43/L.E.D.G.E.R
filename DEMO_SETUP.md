# L.E.D.G.E.R. Local Demo

## Prerequisites

- Python 3.11 or newer
- Node.js 22.12 or newer (Vite 8 requirement) and npm
- PowerShell on Windows

Run commands from the repository root unless noted. The API is `http://127.0.0.1:8000`; Vite is `http://127.0.0.1:5173`.

For the stabilized integration checkout, use `integration/admin-frontend-complete`. The frontend displays COUNT results as whole counts using the backend's `COUNT(*)` formula metadata; monetary results continue to use the backend currency metadata.

## Install and initialize

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:LEDGER_DB_PATH = "data/demo_ledger.db"
python -m database.ingestion
```

Ingestion initializes the SQLite schema, then loads sample users, expenses, and budgets from `data/`. Invalid CSV rows are reported and rejected by the existing validators; they are intentionally retained in the source CSVs. The application uses the same `database.connection.get_connection()` for authentication, ingestion, and expense calculations. The demo uses `data/demo_ledger.db`; set `LEDGER_DB_PATH` to the same path before initialization and API startup. Without the override, the default is `data/ledger.db`.

## Configure and start

The frontend defaults to `http://127.0.0.1:8000`. If you need a different API URL, create `frontend/.env.local` with `VITE_API_BASE_URL=http://127.0.0.1:8000`. `.env.example` documents backend settings; export variables explicitly in PowerShell because the app does not automatically read a `.env` file:

```powershell
$env:LEDGER_DB_PATH = "data/demo_ledger.db"
$env:LEDGER_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
$env:LEDGER_COOKIE_SECURE = "false"
$env:LEDGER_SESSION_SECRET = (python -c "import secrets; print(secrets.token_urlsafe(32))")
# Optional Google OAuth. Leave these unset to disable the Google sign-in button.
# $env:GOOGLE_CLIENT_ID = "..."
# $env:GOOGLE_CLIENT_SECRET = "..."
# $env:GOOGLE_REDIRECT_URI = "http://127.0.0.1:8000/auth/google/callback"
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). Health endpoint: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health). The session cookie contains only a signed user ID; the role and cost centre are reloaded from SQLite for every API request. Use HTTPS and set `LEDGER_COOKIE_SECURE=true` outside local HTTP demos.

Google sign-in is disabled unless a client ID, client secret, and exact callback URI are configured with Google. OAuth links only verified Google emails to an account already provisioned in the LEDGER users table; it does not create accounts or assign roles. Register the callback URI with Google. With no credentials, the UI keeps the Google button disabled and `/auth/google/login` returns 503.

## Demo accounts and queries

Sample data uses the documented development password `Password123!` (also used by the repository authentication tests):

| Role | Email | User ID |
|---|---|---|
| Employee | `akanksha@example.com` | `U003` |
| Manager | `shaurya@example.com` | `U001` |
| Admin | `divyapunj@example.com` | `U005` |

Use a sample Employee for own-expense queries, a Manager for cost-centre queries, and an Admin for organization expense queries. Example prompts supported by the compiler include:

- `How much did I spend on Food this month?`
- `Show my top 5 Travel expenses this month.`
- `How many Food expenses did I submit this month?`
- `How much did I spend on Travel in August 2026?` (the sample employee has no authorized Travel rows in August; the UI reports no matches rather than implying spend)

Manager/Admin may also ask `How much did we spend on Food this month?`. Budget questions are limited to cost-centre budget scope; Employee and organization-level budgets are unsupported because the budget table has no corresponding dimensions.

Successful responses show the calculated result, formula, audit ID, and authorized expense IDs. The admin audit endpoints are `/audit/recent` and `/audit/{query_id}`. No credentials or password hashes are returned to the browser.

The dashboard loads real aggregates from `/analytics/overview` for monthly and category spending; totals stay separated by currency. Budget comparison is unavailable because the budget table has no currency column. Add Expense posts only category, amount, currency, date, and optional description; the backend takes identity and cost centre from the authenticated session. Admins can use the Admin Portal to search/filter users, provision accounts, and persist role or cost-centre updates. Those routes enforce backend Admin permissions and write audit records. New account passwords must contain at least 12 characters.

With the checked-in sample data, the Employee 2026 expense-count query returns `2` (source IDs `EXP-1029` and `EXP-1005`). The Manager Food/September query returns `INR 7,167` from four `CC-TECH` expense rows. The Admin organization query returns `INR 13,637` from six authorized rows.

## Security demo

- Login uses the SQLite `users` table and bcrypt, with generic invalid-credential responses.
- The frontend query schema accepts only `prompt` and optional `current_date`; try adding `user_id`, `role`, `scope`, `scope_value`, or `cost_centre` to `/query/execute` JSON. Extra fields are rejected.
- Scope comes from the database-backed authenticated identity and the centralized RBAC matrix. Employee scope is the user ID; Manager scope is the assigned cost centre; Admin expense scope is organization-wide.
- CORS permits only the configured localhost frontend origin and credentials. Do not use wildcard origins with session cookies.
- Query calculations use parameterized database access. Successful relevant queries are persisted to the SQLite audit database at `data/audit.db`.

## Troubleshooting

- If login returns 401, confirm ingestion completed and that the email is copied exactly from `data/sample_users.csv` with the development password above.
- If browser API requests fail, check that both servers are running, that `VITE_API_BASE_URL` is `http://127.0.0.1:8000`, and that `LEDGER_CORS_ORIGINS` includes the exact browser origin (`http://127.0.0.1:5173` or `http://localhost:5173`).
- If a port is busy, change the Vite/backend port and update CORS plus `frontend/.env.local` accordingly.
- If SQLite reports missing tables, rerun `python -m database.ingestion` using the same `LEDGER_DB_PATH` used by the backend.
- `npm run build` compiles TypeScript and creates the production frontend bundle in `frontend/dist`.

## Test suite

Install test tools and run the complete suite from the repository root:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```
