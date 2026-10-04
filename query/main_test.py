"""
main_test.py — Standalone test app for YOUR module only.

This is NOT the team's real app.py — it exists so you can run and test
your Query Compiler's API endpoint in isolation, before it gets plugged
into the team's combined FastAPI app.

Run with:
    uvicorn main_test:app --reload

Then open http://127.0.0.1:8000/docs in a browser for interactive testing,
or use curl (see the comment at the bottom of this file).
"""

from fastapi import FastAPI

from .api import router

app = FastAPI(title="LEDGER Query Compiler (standalone test)")
app.include_router(router)


# Example curl test, once the server is running:
#
# curl -X POST http://127.0.0.1:8000/query/compile \
#   -H "Content-Type: application/json" \
#   -d '{"prompt": "How much did I spend on food this month?", "user_scope": "CC-TECH"}'