"""
Unit tests for engine.runtime.errors.
No filesystem access — pure class behaviour.
"""
import pytest
from engine.runtime.errors import (
    RuntimeErrorBase,
    GovernanceError,
    PathForbiddenError,
    ManifestError,
    SkillError,
    RuntimeExecutionError,
)


class TestRuntimeErrorBase:
    def test_message_stored(self):
        e = ManifestError("bad manifest")
        assert e.message == "bad manifest"
        assert str(e) == "bad manifest"

    def test_context_defaults_to_empty_dict(self):
        e = ManifestError("x")
        assert e.context == {}

    def test_context_stored(self):
        e = ManifestError("x", context={"key": "val"})
        assert e.context == {"key": "val"}

    def test_to_dict_shape(self):
        e = ManifestError("bad", context={"a": 1})
        d = e.to_dict()
        assert d["error_type"] == "ManifestError"
        assert d["message"] == "bad"
        assert d["context"] == {"a": 1}


class TestGovernanceError:
    def test_is_subclass_of_runtime_error_base(self):
        assert issubclass(GovernanceError, RuntimeErrorBase)

    def test_is_exception(self):
        with pytest.raises(GovernanceError):
            raise GovernanceError("violation")


class TestPathForbiddenError:
    def test_is_governance_error(self):
        assert issubclass(PathForbiddenError, GovernanceError)

    def test_message_includes_path(self):
        e = PathForbiddenError("governance/foo.json")
        assert "governance/foo.json" in e.message

    def test_context_has_forbidden_path(self):
        e = PathForbiddenError("governance/foo.json")
        assert e.context["forbidden_path"] == "governance/foo.json"

    def test_path_attribute(self):
        e = PathForbiddenError("governance/foo.json")
        assert e.path == "governance/foo.json"


class TestSkillError:
    def test_message_includes_skill_name_and_reason(self):
        e = SkillError("my_skill", "not found")
        assert "my_skill" in e.message
        assert "not found" in e.message

    def test_context_keys(self):
        e = SkillError("my_skill", "not found")
        assert e.context["skill_name"] == "my_skill"
        assert e.context["reason"] == "not found"

    def test_skill_name_attribute(self):
        e = SkillError("my_skill", "not found")
        assert e.skill_name == "my_skill"


class TestErrorHierarchy:
    def test_path_forbidden_caught_as_governance(self):
        with pytest.raises(GovernanceError):
            raise PathForbiddenError("governance/x")

    def test_manifest_error_not_governance(self):
        with pytest.raises(ManifestError):
            raise ManifestError("schema fail")
        # ManifestError must NOT be a GovernanceError
        assert not issubclass(ManifestError, GovernanceError)

    def test_all_errors_have_to_dict(self):
        errors = [
            GovernanceError("g"),
            PathForbiddenError("p"),
            ManifestError("m"),
            SkillError("s", "r"),
            RuntimeExecutionError("e"),
        ]
        for e in errors:
            d = e.to_dict()
            assert "error_type" in d
            assert "message" in d
            assert "context" in d
