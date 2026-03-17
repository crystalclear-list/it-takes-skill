from typing import List, Any, Tuple, Dict

from engine.runtime.errors import RuntimeExecutionError, SkillError


def execute(skills: List[Any], input_data: Dict) -> Tuple[Dict, List[str]]:
    """
    Executes skills sequentially, passing the output of each skill
    as the input to the next.

    Each skill module must expose:
        run(data: dict) -> dict

    Returns:
        result: final data dict after all skills
        events: list of log strings describing execution steps
    """

    if not isinstance(input_data, dict):
        raise RuntimeExecutionError(
            "Executor expected input_data to be a dict",
            context={"type": str(type(input_data))}
        )

    events: List[str] = []
    data: Dict = input_data

    for skill in skills:
        skill_name = getattr(skill, "__name__", str(skill))

        events.append(f"Executing skill: {skill_name}")

        run_fn = getattr(skill, "run", None)
        if run_fn is None or not callable(run_fn):
            raise SkillError(
                f"Skill '{skill_name}' is missing a callable run(data: dict) -> dict",
                context={"skill_name": skill_name}
            )

        try:
            result = run_fn(data)
        except Exception as e:
            raise RuntimeExecutionError(
                f"Skill '{skill_name}' raised an exception during execution",
                context={"skill_name": skill_name, "error": str(e)}
            )

        if not isinstance(result, dict):
            raise RuntimeExecutionError(
                f"Skill '{skill_name}' returned a non-dict result",
                context={"skill_name": skill_name, "result_type": str(type(result))}
            )

        data = result
        events.append(f"Skill '{skill_name}' completed successfully")

    return data, events
