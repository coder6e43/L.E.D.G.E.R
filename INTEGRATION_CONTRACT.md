# LEDGER - Integration Contract

## 1. Authentication / RBAC Output

The Authentication + RBAC module provides the authenticated user's trusted identity and authorization scope.

Example:

{
    "user_id": "U001",
    "role": "Manager",
    "cost_centre": "CC-TECH"
}

---

## 2. Query Compiler Output

The Query Compiler converts natural-language questions into a structured query.

Example:

{
    "intent": "sum_expenses",
    "category": "Food",
    "date_start": "2026-09-01",
    "date_end": "2026-09-30"
}

The Query Compiler must not perform financial calculations.

---

## 3. Calculation Engine Input

The Calculation Engine receives:

- Structured query
- Authenticated user context
- Authorized cost-centre scope

Example:

{
    "intent": "sum_expenses",
    "category": "Food",
    "date_start": "2026-09-01",
    "date_end": "2026-09-30",
    "user_id": "U001",
    "authorized_cost_centre": "CC-TECH"
}

---

## 4. Calculation Engine Output

Example:

{
    "result": 4820,
    "currency": "INR",
    "source_rows": [
        "EXP-1002",
        "EXP-1042",
        "EXP-1088"
    ]
}

---

## 5. Security Rule

The frontend must never be trusted to define the user's authorized cost centre.

The backend must determine the user's identity, role and authorized scope.

Unauthorized access must be rejected.

---

## 6. Core Architecture

User
↓
Authentication
↓
RBAC / Authorization
↓
Query Compiler
↓
Authorized Query
↓
Database
↓
Deterministic Calculation
↓
Audit
↓
Frontend

## Database Module (Divyapunj) — how to use it

**Do not open your own sqlite3 connection.** Always import the shared one:

```python
from database.connection import get_connection

with get_connection() as conn:
    rows = conn.execute("SELECT * FROM expenses WHERE cost_centre = ?", ("CC-TECH",)).fetchall()
    for row in rows:
        print(row["expense_id"], row["amount"])  # row acts like a dict
```

This handles commit/rollback/close for you automatically — don't manage transactions yourself.

### Tables available

**`users`** — Shubham (Auth/RBAC) reads this
| column | type | notes |
|---|---|---|
| user_id | TEXT (PK) | |
| name | TEXT | |
| email | TEXT | unique |
| password_hash | TEXT | never store plaintext |
| role | TEXT | `Manager` / `Employee` / `Admin` |
| cost_centre | TEXT | the ONE authorized cost centre for this user |

**`expenses`** — Shaurya (Calculation) reads this
| column | type | notes |
|---|---|---|
| expense_id | TEXT (PK) | |
| user_id | TEXT | FK → users.user_id |
| cost_centre | TEXT | filter on this for RBAC scoping |
| category | TEXT | one of 8 fixed categories (see ingestion.py `ALLOWED_CATEGORIES`) |
| amount | REAL | always ≥ 0 |
| currency | TEXT | INR / USD / EUR |
| date | TEXT | ISO format `YYYY-MM-DD` |
| description | TEXT | free text |

**`budgets`** — Shaurya (Calculation) reads this
| column | type | notes |
|---|---|---|
| budget_id | TEXT (PK) | |
| cost_centre | TEXT | |
| category | TEXT | |
| amount | REAL | budget ceiling |
| period_start / period_end | TEXT | ISO dates defining the budget period |

### Example: Shaurya's calculation engine pattern

```python
from database.connection import get_connection

def total_spent(cost_centre: str, category: str, date_start: str, date_end: str) -> float:
    with get_connection() as conn:
        row = conn.execute(
            """SELECT SUM(amount) as total FROM expenses
               WHERE cost_centre = ? AND category = ? AND date BETWEEN ? AND ?""",
            (cost_centre, category, date_start, date_end),
        ).fetchone()
        return row["total"] or 0.0
```

### Example: Shubham's RBAC lookup pattern

```python
from database.connection import get_connection

def get_user(user_id: str):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
```

### Rules
- Never trust a `cost_centre` value coming from the frontend or the LLM — always resolve it server-side from `users.cost_centre` via this module.
- The LLM must never write SQL directly against these tables; it only produces the structured JSON query (Niketan's job), which Shaurya's code turns into parameterized queries like above.
- To reload/reset test data locally: delete `data/ledger.db` and run `python -m database.ingestion`.
- Sample data covers 3 cost centres (CC-TECH, CC-MARKETING, CC-SALES), 2 months (Aug/Sept 2026), all 8 categories — enough to demo filters, sums, and budget-burn calculations.