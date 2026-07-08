"""Eval-runner endpoint: run the offline eval suite on demand (also run in CI)."""
from __future__ import annotations

from fastapi import APIRouter

from evals.runner import run_suite

router = APIRouter()


@router.post("/evals/run")
def run() -> dict:
    return run_suite()
