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