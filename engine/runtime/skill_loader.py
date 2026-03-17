"""
Skill prompt loader.
Skills are .md files — system prompts for the Claude API, not Python modules.
Searches all four skill layers in priority order: atomic → molecular → system → meta.
"""

from __future__ import annotations

from pathlib import Path

from engine.runtime.errors import SkillError

_SKILL_ROOTS = [
    Path("skills/atomic"),
    Path("skills/molecular"),
    Path("skills/system"),
    Path("skills/meta"),
]


def load_prompt(skill_name: str) -> str:
    """
    Loads the .md file for `skill_name` from the first matching skill layer.
    Raises SkillError if the skill is not found in any layer.
    """
    for root in _SKILL_ROOTS:
        candidate = root / f"{skill_name}.md"
        if candidate.exists():
            return candidate.read_text()

    raise SkillError(
        skill_name,
        f"Not found in any skill layer. Searched: {[str(r) for r in _SKILL_ROOTS]}",
    )


def resolve_steps(manifest: dict) -> list[dict]:
    """
    Enriches each step with its 'skill_prompt' field.
    Steps without a 'skill' key pass context through unchanged.
    """
    resolved = []
    for step in manifest["steps"]:
        skill_name = step.get("skill")
        if skill_name:
            prompt = load_prompt(skill_name)
            resolved.append({**step, "skill_prompt": prompt})
        else:
            resolved.append({**step, "skill_prompt": None})
    return resolved
