import os
from datetime import datetime, timezone

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

app = FastAPI(title="Approval API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "n8n")
POSTGRES_USER = os.getenv("POSTGRES_USER", "n8n")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "n8n")


def get_conn():
    return psycopg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        autocommit=True,
    )


class ApprovalDecision(BaseModel):
    reviewer: str = Field(min_length=1)
    decision: str = Field(pattern="^(approved|rejected)$")
    note: str = ""


@app.get("/health")
def health():
    return {"status": "ok", "service": "approval-api"}


@app.get("/approvals")
def list_approvals(status: str = "pending"):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, task_id, action, proposed_by, confidence, status, reason, reviewer, created_at, reviewed_at
                    FROM approvals
                    WHERE status = %s
                    ORDER BY created_at ASC
                    """,
                    (status,),
                )
                rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "task_id": r[1],
                "action": r[2],
                "proposed_by": r[3],
                "confidence": float(r[4]),
                "status": r[5],
                "reason": r[6],
                "reviewer": r[7],
                "created_at": r[8].isoformat(),
                "reviewed_at": r[9].isoformat() if r[9] else None,
            }
            for r in rows
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/approvals/{approval_id}/decision")
def review_approval(approval_id: int, payload: ApprovalDecision):
    decision_status = "approved" if payload.decision == "approved" else "rejected"
    now = datetime.now(timezone.utc)

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT task_id, action, status FROM approvals WHERE id = %s
                    """,
                    (approval_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Approval not found")
                task_id, action, current_status = row
                if current_status != "pending":
                    raise HTTPException(status_code=400, detail="Approval already reviewed")

                cur.execute(
                    """
                    UPDATE approvals
                    SET status = %s, reviewer = %s, reason = %s, reviewed_at = %s
                    WHERE id = %s
                    """,
                    (decision_status, payload.reviewer, payload.note, now, approval_id),
                )

                execution_status = "executed" if decision_status == "approved" else "blocked"
                details = "Approved by human reviewer" if decision_status == "approved" else "Rejected by human reviewer"
                cur.execute(
                    """
                    INSERT INTO execution_results (task_id, action, execution_status, details)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (task_id, action, execution_status, details),
                )

        return {
            "approval_id": approval_id,
            "task_id": task_id,
            "decision": decision_status,
            "reviewed_at": now.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
