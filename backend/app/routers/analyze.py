from __future__ import annotations

import hashlib
import logging

from fastapi import APIRouter, HTTPException

from app.ai import orchestrator
from app.cache import cache_get, cache_set
from app.config import get_settings
from app.db import store
from app.schemas.report import AnalyzeRequest, QARequest, QAResponse, Report

logger = logging.getLogger(__name__)
router = APIRouter()


def _report_cache_key(req: AnalyzeRequest) -> str:
    body = f"{req.address.lower().strip()}|{req.purchase_price}|{req.down_payment_pct}|{req.intent}"
    return "report:" + hashlib.sha256(body.encode()).hexdigest()[:24]


@router.post("/analyze", response_model=Report)
def analyze(req: AnalyzeRequest) -> dict:
    key = _report_cache_key(req)
    cached = cache_get(key)
    if cached:
        return cached

    try:
        report = orchestrator.generate_report(req)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not report.get("property_facts", {}).get("square_footage") and not report.get("payment_model"):
        # Nothing resolved for this address — don't cache a useless report
        raise HTTPException(
            status_code=404,
            detail="No property data found for that address. Check the format: '123 Main St, City, ST 12345'.",
        )

    cache_set(key, report, get_settings().report_cache_ttl)
    cache_set(f"report:id:{report['report_id']}", report, get_settings().report_cache_ttl)
    store.save_report(report)
    return report


@router.get("/reports/{report_id}", response_model=Report)
def get_report(report_id: str) -> dict:
    report = cache_get(f"report:id:{report_id}") or store.load_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found or expired")
    return report


@router.post("/qa", response_model=QAResponse)
def qa(req: QARequest) -> dict:
    report = cache_get(f"report:id:{req.report_id}") or store.load_report(req.report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found or expired")
    result = orchestrator.answer_question(report, req.question)
    return {"answer": result["answer"], "source_ids": result["source_ids"]}
