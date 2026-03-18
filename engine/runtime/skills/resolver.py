import importlib
from typing import List, Any

from engine.runtime.errors import SkillError, GovernanceError


def resolve_skills(manifest: dict) -> List[Any]:
    """
    Resolves skills listed in the manifest into executable modules.

    Expects manifest["skills"] to be a list of skill names (strings),
    where each skill corresponds to a Python module under skills/.

    Each skill module MUST expose a callable `run(data: dict) -> dict`.
    """

    if "skills" not in manifest or not isinstance(manifest["skills"], list):
        raise GovernanceError(
            "Manifest is missing a valid 'skills' list",
            context={"manifest_name": manifest.get("name")}
        )

    resolved = []

    for skill_name in manifest["skills"]:
        if not isinstance(skill_name, str) or not skill_name.strip():
            raise SkillError(
                "Skill name must be a non-empty string",
                context={"skill_name": skill_name}
            )

        module_path = f"skills.{skill_name}"

        try:
            module = importlib.import_module(module_path)
        except Exception as e:
            raise SkillError(
                f"Failed to import skill module '{module_path}'",
                context={"skill_name": skill_name, "error": str(e)}
            )

        # Ensure `run` exists and is callable
        run_fn = getattr(module, "run", None)
        if run_fn is None or not callable(run_fn):
            raise SkillError(
                f"Skill '{skill_name}' is missing a callable run(data: dict) -> dict",
                context={"skill_name": skill_name}
            )

        resolved.append(module)

    return resolved
