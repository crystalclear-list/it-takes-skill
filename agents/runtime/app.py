import json
import os
from datetime import datetime, timezone

import httpx
import psycopg
import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Agent Runtime", version="1.0.0")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "n8n")
POSTGRES_USER = os.getenv("POSTGRES_USER", "n8n")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "n8n")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
POLICY_MIN_CONFIDENCE = float(os.getenv("POLICY_MIN_CONFIDENCE", "0.6"))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "tinyllama")

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def get_conn():
    return psycopg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        autocommit=True,
    )


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)
    model: str = DEFAULT_MODEL
    stream: bool = False


class Proposal(BaseModel):
    task_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    agent_name: str = "decision-agent"


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "agent-runtime",
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/propose")
def propose(payload: Proposal):
    requires_review = payload.confidence < POLICY_MIN_CONFIDENCE
    policy_result = "requires_human_review" if requires_review else "auto_execute"

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO agent_decisions (task_id, agent_name, action, confidence, policy_result)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        payload.task_id,
                        payload.agent_name,
                        payload.action,
                        payload.confidence,
                        policy_result,
                    ),
                )

                if requires_review:
                    cur.execute(
                        """
                        INSERT INTO approvals (task_id, action, proposed_by, confidence, status, reason)
                        VALUES (%s, %s, %s, %s, 'pending', %s)
                        RETURNING id
                        """,
                        (
                            payload.task_id,
                            payload.action,
                            payload.agent_name,
                            payload.confidence,
                            f"confidence_below_{POLICY_MIN_CONFIDENCE}",
                        ),
                    )
                    approval_id = cur.fetchone()[0]
                else:
                    cur.execute(
                        """
                        INSERT INTO execution_results (task_id, action, execution_status, details)
                        VALUES (%s, %s, 'executed', %s)
                        """,
                        (
                            payload.task_id,
                            payload.action,
                            "Auto-executed because confidence met policy threshold",
                        ),
                    )
                    approval_id = None

        event = {
            "event": "task.proposed",
            "task_id": payload.task_id,
            "agent": payload.agent_name,
            "confidence": payload.confidence,
            "requires_review": requires_review,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        redis_client.lpush("agent_tasks", json.dumps(event))
        redis_client.publish("agent_events", json.dumps(event))

        return {
            "task_id": payload.task_id,
            "policy_result": policy_result,
            "requires_approval": requires_review,
            "approval_id": approval_id,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/generate")
def generate(payload: GenerateRequest):
    """Send a prompt to Ollama and return the generated response."""
    try:
        resp = httpx.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": payload.model, "prompt": payload.prompt, "stream": False},
            timeout=120.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "model": payload.model,
            "prompt": payload.prompt,
            "response": data.get("response", ""),
            "done": data.get("done", True),
        }
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Model '{payload.model}' not found. Pull it first: docker compose exec ollama ollama pull {payload.model}",
            ) from exc
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"Ollama unreachable: {exc}") from exc
