"""
Typed error hierarchy for the Skill OS runtime.
All errors halt execution — no silent failures.

Hierarchy:
  RuntimeError
    └── GovernanceError       base — any governance boundary violation
          ├── ForbiddenPathError   write to a forbidden path
          ├── ManifestError        manifest missing, invalid, or schema-failing
          └── SkillError           skill not found or execution failed
"""


class GovernanceError(RuntimeError):
    """
    Base class for all governance violations.
    halt_on_violation = True is always in effect.
    Catching this without re-raising is itself a violation.
    """


class ForbiddenPathError(GovernanceError):
    """Raised when a write is attempted to a path in forbidden_paths.json."""

    def __init__(self, path: str) -> None:
        super().__init__(
            f"Write to '{path}' is forbidden by governance/forbidden_paths.json. "
            "halt_on_violation=True."
        )
        self.path = path


class ManifestError(GovernanceError):
    """Raised when a manifest is missing, malformed, or fails schema validation."""

    def __init__(self, message: str) -> None:
        super().__init__(f"ManifestError: {message}")


class SkillError(GovernanceError):
    """Raised when a skill cannot be loaded or the API call for it fails."""

    def __init__(self, skill_name: str, reason: str) -> None:
        super().__init__(f"SkillError for '{skill_name}': {reason}")
        self.skill_name = skill_name
