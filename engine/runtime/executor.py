"""
Step executor — calls the Claude API for each skill-bearing step.
Passes output of each step as input to the next (pipeline pattern).
Raises SkillError on API failure — halt_on_violation=True.
"""

from __future__ import annotations

import json
from typing import Any

import anthropic

from engine.runtime.errors import RuntimeExecutionError, SkillError

MODEL = "claude-sonnet-4-6"


def execute_steps(
    steps: list[dict],
    input_data: dict,
    run_id: str,
    events: list[dict],
    log_event_fn,
) -> tuple[Any, list[dict]]:
    """
    Executes steps sequentially via the Claude API.
    Steps without a skill_prompt pass context through unchanged.
    Returns (final_context, updated_events).
    """
    client = anthropic.Anthropic()
    context = input_data

    for step in steps:
        step_id = step["id"]
        skill_prompt = step.get("skill_prompt")

        log_event_fn(events, run_id, step["agent_id"], "step_start", {
            "step_id": step_id,
            "agent_role": step["agent_role"],
            "has_skill": skill_prompt is not None,
        })

        if skill_prompt is None:
            log_event_fn(events, run_id, step["agent_id"], "step_skip", {
                "step_id": step_id,
                "reason": "no skill declared — context passed through",
            })
            continue

        user_message = json.dumps(context, indent=2)

        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=skill_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
        except Exception as exc:
            raise SkillError(
                step.get("skill", step_id),
                f"Claude API call failed: {exc}",
            )

        try:
            output_text = response.content[0].text
        except (IndexError, AttributeError) as exc:
            raise RuntimeExecutionError(
                f"Unexpected API response structure at step '{step_id}': {exc}",
                context={"step_id": step_id},
            )

        try:
            context = json.loads(output_text)
        except json.JSONDecodeError:
            context = {"output": output_text, "step_id": step_id}

        log_event_fn(events, run_id, step["agent_id"], "step_complete", {
            "step_id": step_id,
            "output_preview": output_text[:200],
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        })

    return context, events
