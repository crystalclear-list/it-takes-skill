"""
Unit tests for engine.runtime.io.path_guard.
Requires governance/forbidden_paths.json to be present.
"""
import pytest
from engine.runtime.errors import PathForbiddenError
from engine.runtime.io.path_guard import _assert_path_allowed


class TestPathGuard:
    def test_allowed_path_does_not_raise(self):
        _assert_path_allowed("reports/some_output.json")      # should pass
        _assert_path_allowed("logs/workflows/run.log")         # should pass

    def test_governance_path_raises(self):
        with pytest.raises(PathForbiddenError):
            _assert_path_allowed("governance/safety-rules.md")

    def test_agents_core_path_raises(self):
        with pytest.raises(PathForbiddenError):
            _assert_path_allowed("agents/core/audit.json")

    def test_manifests_workflows_raises(self):
        with pytest.raises(PathForbiddenError):
            _assert_path_allowed("manifests/workflows/anything.json")

    def test_git_path_raises(self):
        with pytest.raises(PathForbiddenError):
            _assert_path_allowed(".git/config")

    def test_engine_path_raises(self):
        with pytest.raises(PathForbiddenError):
            _assert_path_allowed("engine/runtime/api.py")

    def test_accepts_str_and_path(self):
        from pathlib import Path
        _assert_path_allowed(Path("reports/x.json"))
        _assert_path_allowed("reports/x.json")
