"""
schema.py — Query Compiler module (Niketan)

Pydantic schemas for the structured query object, plus the category
synonym dictionary used to normalize free-text category mentions.
This is the single source of truth for what a "valid query" looks like.
"""

from __future__ import annotations
from enum import Enum
from datetime import date
from typing import Optional

from pydantic import BaseModel, field_validator


# ---------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------

class Intent(str, Enum):
    sum_expenses = "sum_expenses"
    category_breakdown = "category_breakdown"
    top_transactions = "top_transactions"
    count_expenses = "count_expenses"
    remaining_budget = "remaining_budget"
    source_lookup = "source_lookup"


class Status(str, Enum):
    SUCCESS = "SUCCESS"
    CLARIFY = "CLARIFY"
    REFUSED = "REFUSED"


# ---------------------------------------------------------------------
# Core query object
# ---------------------------------------------------------------------

class Query(BaseModel):
    """The validated, structured query produced by the compiler.
    This is exactly what gets handed to the Database + Calculation Engine.
    """
    intent: Intent
    user_scope: str                      # inherited from session; NEVER set from the prompt
    category: Optional[str] = None
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    limit: Optional[int] = None
    currency: str = "INR"

    @field_validator("date_range_end")
    @classmethod
    def check_date_order(cls, end_date, info):
        start_date = info.data.get("date_range_start")
        if start_date and end_date and end_date < start_date:
            raise ValueError("date_range_end cannot be before date_range_start")
        return end_date

    @field_validator("limit")
    @classmethod
    def check_limit_range(cls, limit_value):
        if limit_value is not None and not (1 <= limit_value <= 50):
            raise ValueError("limit must be between 1 and 50")
        return limit_value


class CompilerResponse(BaseModel):
    """What compile_query() returns. `query` is only set when status is
    SUCCESS; `message` is set for CLARIFY / REFUSED so the frontend can
    display it."""
    status: Status
    query: Optional[Query] = None
    message: Optional[str] = None


# ---------------------------------------------------------------------
# Category synonym dictionary
# ---------------------------------------------------------------------

CATEGORY_SYNONYMS = {
    "Food": [
        "food", "dining", "meals", "lunch", "dinner", "breakfast",
        "client lunch", "client dinner", "coffee", "catering", "refreshments",
    ],

    "Travel": [
        "travel", "flight", "airfare", "hotel", "lodging", "uber",
        "taxi", "cab", "cab fare", "train", "train ticket",
        "conveyance", "mileage", "per diem", "client visit",
        "client visit cab fare", "fuel reimbursement",
    ],

    "Software": [
        "software", "saas", "subscriptions", "licenses", "cloud",
        "aws", "github", "slack", "zoom", "tools", "hosting",
        "dev tools", "dev tools license", "ide license",
        "annual ide license", "cloud hosting",
    ],

    "Office Supplies": [
        "office supplies", "stationery", "printing", "paper",
        "desk supplies", "toner", "courier", "postage",
        "whiteboard markers", "printer cartridges",
    ],

    "Training": [
        "training", "conference", "seminar", "course", "certification",
        "workshop", "professional development", "certification exam",
        "workshop fee", "online course",
    ],

    "Marketing": [
        "marketing", "ad campaign", "advertising", "ads",
        "campaign", "promotion", "social media promo",
    ],

    "Miscellaneous": [
        "miscellaneous", "misc", "other", "team event", "sundry",
        "misc reimbursement",
    ],

    "Utilities": [
        "utilities", "utility", "electricity", "electricity bill",
        "water bill", "phone bill", "internet bill",
    ],

    "Snacks": [
        "snacks", "chips", "biscuits", "vending machine",
    ],
}

CANONICAL_CATEGORIES = list(CATEGORY_SYNONYMS.keys())


def normalize_category(text: str) -> Optional[str]:
    """
    Scan free text for any known synonym and return the canonical
    category name. Returns None if nothing matches.
    """
    text_lower = text.lower()
    for canonical, synonyms in CATEGORY_SYNONYMS.items():
        for synonym in sorted(synonyms, key=len, reverse=True):
            if synonym in text_lower:
                return canonical
    return None


def mentions_unknown_category(text: str) -> bool:
    """
    Heuristic for the 'Unmapped Category' refusal case: True if the text
    looks like it's asking about a specific category, but that category
    isn't one we recognize.

    Guard: if the trigger phrase is immediately followed by a digit (e.g.
    "spend on 01/09/2026" or "spent on 2026-09-01"), it's referring to a
    date, not a category — don't flag it.
    """
    import re

    trigger_words = ["spend on", "spent on", "expenses for", "budget for", "spending on"]
    text_lower = text.lower()

    has_trigger = any(t in text_lower for t in trigger_words)
    if not has_trigger:
        return False

    followed_by_date = re.search(
        r"(spend on|spent on|expenses for|budget for|spending on)\s+\d",
        text_lower,
    )
    if followed_by_date:
        return False

    has_known_category = normalize_category(text) is not None
    return not has_known_category