import os

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Agent Registry API", version="1.0.0")

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


class AgentRegistration(BaseModel):
    name: str = Field(min_length=1)
    capability: str = Field(min_length=1)
    endpoint: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: str = "active"


@app.get("/health")
def health():
    return {"status": "ok", "service": "registry-api"}


@app.get("/agents")
def list_agents():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, capability, endpoint, version, status, created_at
                    FROM agents
                    ORDER BY id ASC
                    """
                )
                rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "name": r[1],
                "capability": r[2],
                "endpoint": r[3],
                "version": r[4],
                "status": r[5],
                "created_at": r[6].isoformat(),
            }
            for r in rows
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/agents")
def register_agent(payload: AgentRegistration):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO agents (name, capability, endpoint, version, status)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                      capability = EXCLUDED.capability,
                      endpoint = EXCLUDED.endpoint,
                      version = EXCLUDED.version,
                      status = EXCLUDED.status
                    RETURNING id
                    """,
                    (
                        payload.name,
                        payload.capability,
                        payload.endpoint,
                        payload.version,
                        payload.status,
                    ),
                )
                agent_id = cur.fetchone()[0]
        return {"id": agent_id, "name": payload.name, "status": payload.status}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
