"""Thin persistence layer. Every function no-ops gracefully when DATABASE_URL
is unset so the API runs standalone in dev; reports are then only in Redis.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

import psycopg

from app.config import get_settings

logger = logging.getLogger(__name__)


def _connect() -> Optional[psycopg.Connection]:
    url = get_settings().database_url
    if not url:
        return None
    try:
        return psycopg.connect(url, connect_timeout=3)
    except Exception as exc:
        logger.warning("Postgres unavailable: %s", exc)
        return None


def save_report(report: dict) -> None:
    conn = _connect()
    if not conn:
        return
    with conn:
        conn.execute(
            """
            INSERT INTO reports (id, address, intent, report, eval_passed)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET report = EXCLUDED.report,
                                           eval_passed = EXCLUDED.eval_passed
            """,
            (
                report["report_id"],
                report["property_facts"]["address"],
                report.get("intent"),
                json.dumps(report),
                report.get("eval_passed"),
            ),
        )
    conn.close()


def load_report(report_id: str) -> Optional[dict]:
    conn = _connect()
    if not conn:
        return None
    with conn:
        row = conn.execute("SELECT report FROM reports WHERE id = %s", (report_id,)).fetchone()
    conn.close()
    return row[0] if row else None
