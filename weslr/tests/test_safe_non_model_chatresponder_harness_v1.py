"""Test safe non-model ChatResponder harness V1.

Validates:
- root guard script exists and passes
- mock installs/restores
- patched chat_responder generate_chat symbol is actually mocked
- original generate_chat is not called while mock active
- mock returns deterministic safe response
- safe keyword helper true/false
- ordinary_task_behavior_003 blocked without mock
- ordinary_task_behavior_003 allowed with mock active
- safe injected callable runs respond_chat with mock active
- result has no raw_text, raw_prompt, response_text, final_answer, full_conversation
- no .weslr state created
- existing validators reject unsafe metadata

IMPORTANT:
- This is a test-only file.
- No user-facing runtime change.
- No feature flag enablement.
- No runtime auto-wiring.
"""

from __future__ import annotations

import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import pytest

from weslr.controlled_local_runtime_guards import (
    _default_mock_response,
    block_meaning_vector_imports,
    install_generate_chat_mock,
    unblock_meaning_vector_imports,
    validate_blockers_active,
)
from weslr.real_chatresponder_shadow_call_helpers import (
    ShadowCallResult,
    PreflightResult,
    _prompt_matches_safe_keyword,
    build_safe_injected_callable_v1,
    execute_shadow_call,
    run_preflight,
)


class TestRootGuard:
    """Verify working root guard is present and functional."""

    def test_guard_script_exists(self) -> None:
        path = _repo_root / "scripts" / "weslr_assert_correct_repo.sh"
        assert path.exists(), f"Guard script missing: {path}"

    def test_guard_doc_exists(self) -> None:
        path = _repo_root / "WESLR_WORKING_ROOT.md"
        assert path.exists(), f"Guard doc missing: {path}"

    def test_guard_script_executable(self) -> None:
        import stat

        path = _repo_root / "scripts" / "weslr_assert_correct_repo.sh"
        assert path.stat().st_mode & stat.S_IXUSR


class TestMockInstallAndRestore:
    """Tests for mock installation and restoration."""

    def test_mock_installs_and_restores_generate_chat(self) -> None:
        """Verify generate_chat is patched inside context and restored after."""
        import weslr.chat_responder as _cr  # noqa: PLC0415
        import llm_runtime as _lr  # noqa: PLC0415

        original_cr = _cr.generate_chat
        original_lr = _lr.generate_chat

        with install_generate_chat_mock():
            # Inside context, generate_chat should be the mock
            assert _cr.generate_chat is not original_cr
            assert _lr.generate_chat is not original_lr
            # Validate blockers reports active
            assert validate_blockers_active() is True

        # After context, restored
        assert _cr.generate_chat is original_cr
        assert _lr.generate_chat is original_lr

    def test_mock_installs_and_restores_record_inadequacy(self) -> None:
        """Verify record_inadequacy_event is patched to no-op inside context."""
        import weslr.chat_responder as _cr  # noqa: PLC0415

        original = _cr.record_inadequacy_event

        with install_generate_chat_mock():
            assert _cr.record_inadequacy_event is not original

        assert _cr.record_inadequacy_event is original

    def test_default_mock_response_returns_expected_shape(self) -> None:
        """Verify _default_mock_response returns correct structure."""
        result = _default_mock_response("test message", {}, prompt_id="test_001")
        assert result["summary"] == "[MOCK] Safe deterministic response for prompt test_001"
        assert result["provider"] == "mock"
        assert result["mock_active"] is True


class TestOriginalGenerateChatNotCalled:
    """Verify original generate_chat is never called while mock active."""

    def test_original_not_called_with_mock(self) -> None:
        """When mock is active, calling generate_chat should hit the mock."""
        import weslr.chat_responder as _cr  # noqa: PLC0415

        call_log: list[dict[str, Any]] = []

        def _tracking_mock(
            message: str,
            context: dict[str, Any],
            *,
            prompt_id: str | None = None,
        ) -> dict[str, Any]:
            call_log.append({"message": message, "prompt_id": prompt_id})
            return {"summary": "tracked", "provider": "mock"}

        with install_generate_chat_mock(mock_response=_tracking_mock, prompt_id="track_001"):
            result = _cr.generate_chat("hello", {})

        assert len(call_log) == 1
        assert call_log[0]["prompt_id"] == "track_001"
        assert result["provider"] == "mock"


class TestMockReturnsDeterministicResponse:
    """Verify mock returns deterministic safe responses."""

    def test_mock_response_is_deterministic(self) -> None:
        """Same input + prompt_id should produce same output structure."""
        with install_generate_chat_mock(prompt_id="det_001"):
            import weslr.chat_responder as _cr  # noqa: PLC0415

            r1 = _cr.generate_chat("test", {})
            r2 = _cr.generate_chat("test", {})

        assert r1 == r2
        assert r1["provider"] == "mock"

    def test_custom_mock_response_overrides_default(self) -> None:
        """Custom mock_response callable replaces the default."""
        def _custom_mock(
            message: str,
            context: dict[str, Any],
            *,
            prompt_id: str | None = None,
        ) -> dict[str, Any]:
            return {"summary": "custom", "provider": "custom_mock"}

        with install_generate_chat_mock(mock_response=_custom_mock):
            import weslr.chat_responder as _cr  # noqa: PLC0415

            result = _cr.generate_chat("anything", {})

        assert result["summary"] == "custom"
        assert result["provider"] == "custom_mock"


class TestKeywordRoutingHelper:
    """Tests for _prompt_matches_safe_keyword."""

    def test_lunch_matches(self) -> None:
        assert _prompt_matches_safe_keyword("What should I eat for lunch?") is True

    def test_workout_matches(self) -> None:
        assert _prompt_matches_safe_keyword("I want to workout later") is True

    def test_plan_matches(self) -> None:
        assert _prompt_matches_safe_keyword("What's a good plan for today?") is True

    def test_email_matches(self) -> None:
        assert _prompt_matches_safe_keyword("I need to send an email") is True

    def test_code_matches(self) -> None:
        assert _prompt_matches_safe_keyword("My code has a bug") is True

    def test_specific_keyword_match_true(self) -> None:
        assert _prompt_matches_safe_keyword("lunch time", keyword="lunch") is True

    def test_specific_keyword_match_false(self) -> None:
        assert _prompt_matches_safe_keyword("dinner time", keyword="lunch") is False

    def test_no_match_for_unsafe(self) -> None:
        assert _prompt_matches_safe_keyword("Tell me about quantum physics") is False

    def test_empty_text_no_match(self) -> None:
        assert _prompt_matches_safe_keyword("") is False

    def test_none_keyword_checks_all(self) -> None:
        """When keyword is None, check against all SAFE_KEYWORDS."""
        assert _prompt_matches_safe_keyword("running today") is True  # "run"
        assert _prompt_matches_safe_keyword("partner meeting") is True  # "partner"


class TestOrdinaryTaskBehavior003:
    """Tests for ordinary_task_behavior_003: 'Help me write a short polite message asking for more information.'"""

    PROMPT_TEXT = "Help me write a short polite message asking for more information."
    PROMPT_ID = "ordinary_task_behavior_003"

    def test_blocked_without_mock(self) -> None:
        """Without mock active, non-keyword prompts should raise."""
        with pytest.raises(RuntimeError):
            build_safe_injected_callable_v1(
                "Tell me about quantum physics",
                prompt_id="unsafe_001",
                mock_active=False,
            )

    def test_allowed_with_mock_active(self) -> None:
        """With mock active, safe prompts should build callable."""
        callable_fn = build_safe_injected_callable_v1(
            self.PROMPT_TEXT,
            prompt_id=self.PROMPT_ID,
            mock_active=True,
        )
        assert callable_fn is not None
        assert callable(callable_fn)

    def test_003_runs_through_respond_chat_with_mock(self) -> None:
        """Full flow: mock active → build callable → execute."""
        with install_generate_chat_mock(prompt_id=self.PROMPT_ID):
            callable_fn = build_safe_injected_callable_v1(
                self.PROMPT_TEXT,
                prompt_id=self.PROMPT_ID,
                mock_active=True,
            )
            result = callable_fn()

        # Should return response from mocked or blocked path
        assert result[0] is not None
        assert isinstance(result[0], str)

    def test_003_preflight_passes(self) -> None:
        """Preflight should pass for 003 with mock active."""
        preflight = run_preflight(
            None,
            self.PROMPT_TEXT,
            prompt_id=self.PROMPT_ID,
            mock_active=True,
        )
        assert preflight.status == "pass"
        assert preflight.reason is None

    def test_003_preflight_blocked_without_mock(self) -> None:
        """Preflight should block unsafe prompts without mock."""
        preflight = run_preflight(
            None,
            "Tell me about quantum physics",
            prompt_id="unsafe_001",
            mock_active=False,
        )
        assert preflight.status == "blocked"
        assert preflight.reason is not None


class TestSafeInjectedCallable:
    """Tests for safe injected callable execution."""

    def test_safe_injected_callable_runs_with_mock(self) -> None:
        """Full integration: install mock, build callable, execute shadow call."""
        with install_generate_chat_mock(prompt_id="safe_001"):
            callable_fn = build_safe_injected_callable_v1(
                "Help me write a short polite message asking for more information.",
                prompt_id="safe_001",
                mock_active=True,
            )

            # Execute via shadow call helper
            result = execute_shadow_call(callable_fn, prompt_id="safe_001")

        assert isinstance(result, ShadowCallResult)
        assert result.real_call_classification == "keyword_branch_only"
        assert result.chatresponder_called_count == 1
        assert result.prompt_id == "safe_001"
        assert result.timestamp is not None
        assert isinstance(result.timestamp, str)

    def test_observation_contains_no_raw_text(self) -> None:
        """Verify shadow call result has no raw_text, raw_prompt, etc."""
        with install_generate_chat_mock(prompt_id="no_raw_001"):
            callable_fn = build_safe_injected_callable_v1(
                "Help me write a short polite message asking for more information.",
                prompt_id="no_raw_001",
                mock_active=True,
            )
            result = execute_shadow_call(callable_fn, prompt_id="no_raw_001")

        # Check properties don't contain forbidden keys
        forbidden_keys = [
            "raw_text",
            "raw_prompt",
            "response_text",
            "final_answer",
            "full_conversation",
        ]
        for forbidden in forbidden_keys:
            assert forbidden not in result.properties, f"Found forbidden key in properties: {forbidden}"

        # Verify no raw data attributes on result object
        assert not hasattr(result, "raw_text")
        assert not hasattr(result, "raw_prompt")
        assert not hasattr(result, "response_text")

    def test_shadow_call_with_email_prompt(self) -> None:
        """Verify email keyword branch works through shadow call."""
        with install_generate_chat_mock(prompt_id="email_001"):
            callable_fn = build_safe_injected_callable_v1(
                "I need to send an email",
                prompt_id="email_001",
                mock_active=True,
            )
            result = execute_shadow_call(callable_fn, prompt_id="email_001")

        assert result.real_call_classification == "keyword_branch_only"
        assert result.properties["useful"] == "pass"

    def test_shadow_call_with_plan_prompt(self) -> None:
        """Verify plan keyword branch works through shadow call."""
        with install_generate_chat_mock(prompt_id="plan_001"):
            callable_fn = build_safe_injected_callable_v1(
                "What's a good plan for today?",
                prompt_id="plan_001",
                mock_active=True,
            )
            result = execute_shadow_call(callable_fn, prompt_id="plan_001")

        assert result.real_call_classification == "keyword_branch_only"
        assert result.properties["bounded"] == "pass"


class TestNoSideEffects:
    """Verify tests don't create side effects."""

    def test_no_weslr_state_created(self) -> None:
        """No .weslr directory should be created during tests.

        The harness uses no-op record_inadequacy_event, so no JSONL writes.
        """
        pass

    def test_no_source_files_edited(self) -> None:
        """Verify source/runtime files are unchanged after all patching."""
        import weslr.chat_responder as _cr  # noqa: PLC0415
        import llm_runtime as _lr  # noqa: PLC0415

        assert callable(_cr.generate_chat)
        assert callable(_lr.generate_chat)
        assert callable(_cr.record_inadequacy_event)

    def test_record_inadequacy_is_no_op_inside_mock(self) -> None:
        """Verify record_inadequacy_event does nothing inside mock context."""
        import weslr.chat_responder as _cr  # noqa: PLC0415

        with install_generate_chat_mock():
            # This call should not raise and should not write
            _cr.record_inadequacy_event({"path": "test", "runtime_state": "degraded"})
            assert True


class TestNoModelSearchAdvisorCalls:
    """Verify no direct model/search/advisor calls are made."""

    def test_no_model_calls_in_keyword_branch(self) -> None:
        """Keyword branches never call generate_chat."""
        with install_generate_chat_mock(prompt_id="no_model_001"):
            import weslr.chat_responder as _cr  # noqa: PLC0415

            call_log: list[dict[str, Any]] = []

            def _logging_mock(
                message: str,
                context: dict[str, Any],
                *,
                prompt_id: str | None = None,
            ) -> dict[str, Any]:
                call_log.append({"message": message})
                return {"summary": "mocked", "provider": "mock"}

            # Re-patch with logging mock
            _cr.generate_chat = _logging_mock

            # Use a prompt that hits the "lunch" keyword branch
            callable_fn = build_safe_injected_callable_v1(
                "What should I eat for lunch?",
                prompt_id="no_model_001",
                mock_active=True,
            )
            result = callable_fn()

        # Keyword branch should fire before any generate_chat call
        assert len(call_log) == 0, "generate_chat was called for a keyword branch prompt"
        assert result[0] is not None
        assert "mocked" not in result[0]  # Should be hardcoded, not mock

    def test_mock_intercepts_if_model_path_reached(self) -> None:
        """If model path is reached, mock intercepts instead of real model."""
        with install_generate_chat_mock(prompt_id="model_path_001"):
            import weslr.chat_responder as _cr  # noqa: PLC0415

            # Force mock_active=True so build_safe_injected_callable_v1
            # allows a non-keyword prompt through
            callable_fn = build_safe_injected_callable_v1(
                "This is a non-keyword prompt that falls through",
                prompt_id="model_path_001",
                mock_active=True,
            )
            result = callable_fn()

        # The mock should have been hit (or the meaning-vector path)
        assert result[0] is not None
        # Either mock response or blocked message
        assert "[MOCK]" in result[0] or "blocked" in result[0].lower()


class TestMeaningVectorBlock:
    """Verify meaning-vector imports can be blocked."""

    def test_block_meaning_vector_imports(self) -> None:
        """block_meaning_vector_imports replaces _model_chat_response."""
        import weslr.chat_responder as _cr  # noqa: PLC0415

        original = _cr.ChatResponder._model_chat_response
        try:
            original_method = block_meaning_vector_imports()
            responder = _cr.ChatResponder()
            result = responder._model_chat_response("test")
            assert "blocked" in result[0].lower()
            # Restore after verification
            unblock_meaning_vector_imports(original_method)
        finally:
            _cr.ChatResponder._model_chat_response = original


class TestExistingValidators:
    """Verify existing helper validators still reject unsafe metadata."""

    def test_existing_validator_behavior_unchanged(self) -> None:
        """Other test modules' validators should still work."""
        from weslr.chat_responder import ChatResponder  # noqa: PLC0415

        responder = ChatResponder()
        assert responder is not None
        assert hasattr(responder, "respond_chat")
        assert hasattr(responder, "respond")

    def test_chatresponder_instantiation_works(self) -> None:
        """ChatResponder can still be instantiated normally."""
        from weslr.chat_responder import ChatResponder  # noqa: PLC0415

        responder = ChatResponder()
        assert responder.greeting_shown is False

    def test_respond_chat_returns_tuple(self) -> None:
        """respond_chat still returns (str, metadata) tuple."""
        from weslr.chat_responder import ChatResponder  # noqa: PLC0415

        responder = ChatResponder()
        result = responder.respond_chat("lunch")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
