import os
from datetime import datetime, timezone

import httpx
from crewai import Agent, Crew, LLM, Task
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="CrewAI Runtime", version="1.0.0")

SAMBANOVA_API_KEY = os.getenv("SAMBANOVA_API_KEY", "")
SAMBANOVA_MODEL = os.getenv("SAMBANOVA_MODEL", "DeepSeek-R1-0528")
AGENT_RUNTIME_URL = os.getenv("AGENT_RUNTIME_URL", "http://agent-runtime:8080")

llm = LLM(
    model=f"openai/{SAMBANOVA_MODEL}",
    base_url="https://api.sambanova.ai/v1",
    api_key=SAMBANOVA_API_KEY,
)

intake_analyst = Agent(
    role="Intake Analyst",
    goal="Analyze incoming tasks and extract key details, risks, and context.",
    backstory=(
        "You are a careful analyst who reads task descriptions and identifies "
        "what action is needed, any risks involved, and how confident you are "
        "in that assessment. You always output structured JSON."
    ),
    llm=llm,
    verbose=False,
)

decision_agent = Agent(
    role="Decision Agent",
    goal="Recommend the best action for a task and provide a confidence score between 0.0 and 1.0.",
    backstory=(
        "You are a decision-making agent. Given an analysis, you recommend a clear "
        "action and score your confidence from 0.0 (very uncertain) to 1.0 (fully certain). "
        "Tasks below 0.6 confidence should go to human review. Output JSON only."
    ),
    llm=llm,
    verbose=False,
)


class RunRequest(BaseModel):
    task_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    agent_name: str = "crewai-agent"


class RunResponse(BaseModel):
    task_id: str
    action: str
    confidence: float
    policy_result: str
    requires_approval: bool
    approval_id: int | None


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "crewai-runtime",
        "model": SAMBANOVA_MODEL,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/run", response_model=RunResponse)
def run(payload: RunRequest):
    if not SAMBANOVA_API_KEY:
        raise HTTPException(status_code=503, detail="SAMBANOVA_API_KEY not set")

    analysis_task = Task(
        description=f"Analyze this task and identify the required action and any risks:\n\n{payload.description}",
        expected_output="A brief analysis with: recommended_action (string) and risk_level (low/medium/high)",
        agent=intake_analyst,
    )

    decision_task = Task(
        description=(
            "Based on the analysis, decide the final action and provide a confidence score.\n"
            "Respond with JSON only: {\"action\": \"<action>\", \"confidence\": <0.0-1.0>}"
        ),
        expected_output='JSON with keys: action (string) and confidence (float 0.0-1.0)',
        agent=decision_agent,
        context=[analysis_task],
    )

    crew = Crew(
        agents=[intake_analyst, decision_agent],
        tasks=[analysis_task, decision_task],
        verbose=False,
    )

    try:
        result = crew.kickoff()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Crew execution failed: {exc}") from exc

    import json, re
    raw = str(result.raw if hasattr(result, "raw") else result)
    action = "review_required"
    confidence = 0.5

    try:
        json_match = re.search(r"\{[^}]+\}", raw, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            action = parsed.get("action", action)
            confidence = float(parsed.get("confidence", confidence))
            confidence = max(0.0, min(1.0, confidence))
    except (json.JSONDecodeError, ValueError):
        pass

    try:
        resp = httpx.post(
            f"{AGENT_RUNTIME_URL}/propose",
            json={
                "task_id": payload.task_id,
                "action": action,
                "confidence": confidence,
                "agent_name": payload.agent_name,
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        propose_result = resp.json()
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"Agent runtime unreachable: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Agent runtime error: {exc.response.text}") from exc

    return RunResponse(
        task_id=payload.task_id,
        action=action,
        confidence=confidence,
        policy_result=propose_result["policy_result"],
        requires_approval=propose_result["requires_approval"],
        approval_id=propose_result.get("approval_id"),
    )
