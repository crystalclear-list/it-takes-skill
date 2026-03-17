"""
Typed error hierarchy for the Skill OS runtime.
All errors halt execution — no silent failures.

Hierarchy:
  RuntimeErrorBase
    ├── GovernanceError           governance rule violated
    │     └── PathForbiddenError  write to a forbidden path
    ├── ManifestError             manifest invalid or schema-failing
    ├── SkillError                skill not found or execution failed
    └── RuntimeExecutionError     unrecoverable internal executor failure
"""


class RuntimeErrorBase(Exception):
    """
    Base class for all runtime-related errors.
    Never raise this directly; use a subclass.
    """

    def __init__(self, message: str, *, context: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def to_dict(self) -> dict:
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
        }


class GovernanceError(RuntimeErrorBase):
    """
    Raised when a governance rule is violated:
    - forbidden write path
    - missing or invalid schema
    - disallowed external behaviour
    halt_on_violation = True is always in effect.
    """


class PathForbiddenError(GovernanceError):
    """
    Raised when a write is attempted to a path in governance/forbidden_paths.json.
    Specialisation of GovernanceError.
    """

    def __init__(self, path: str) -> None:
        super().__init__(
            f"Write to '{path}' is forbidden by governance/forbidden_paths.json. "
            "halt_on_violation=True.",
            context={"forbidden_path": path},
        )
        self.path = path


class ManifestError(RuntimeErrorBase):
    """
    Raised when a manifest is invalid:
    - schema validation failure
    - missing required fields
    - malformed structure
    """


class SkillError(RuntimeErrorBase):
    """
    Raised when a skill cannot be resolved or executed:
    - skill not found in any layer
    - Claude API call failure
    """

    def __init__(self, skill_name: str, reason: str) -> None:
        super().__init__(
            f"SkillError for '{skill_name}': {reason}",
            context={"skill_name": skill_name, "reason": reason},
        )
        self.skill_name = skill_name


class RuntimeExecutionError(RuntimeErrorBase):
    """
    Raised when the runtime itself fails during execution:
    - unexpected exceptions in executor
    - unrecoverable internal errors
    """
