import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import analyze, evals_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="HouseFax API",
    description="AI-generated due-diligence reports for residential properties. "
    "LLM explains. Tools calculate. Database grounds. Evals police.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(evals_router.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
