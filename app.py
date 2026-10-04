from fastapi import FastAPI
from query.api import router as query_router

app = FastAPI(title="LEDGER API")

app.include_router(query_router)