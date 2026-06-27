from __future__ import annotations

from unittest.mock import MagicMock, patch


def _llm(content: str = "response") -> MagicMock:
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content=content)
    return llm


@patch("agents.base.build_llm")
def test_single_round_runs_each_agent_once(mock_build):
    mock_build.return_value = _llm("text")
    from orchestrator.graph import run_debate

    state = run_debate("AI in courts", rounds=1)
    roles = [m["role"] for m in state["transcript"]]
    assert roles == ["proponent", "critic", "analyst", "fact_checker"]
    assert state["status"] == "done"


@patch("agents.base.build_llm")
def test_two_rounds_repeat_the_agent_cycle(mock_build):
    mock_build.return_value = _llm("text")
    from orchestrator.graph import run_debate

    state = run_debate("AI", rounds=2)
    roles = [m["role"] for m in state["transcript"]]
    assert roles == ["proponent", "critic", "analyst", "fact_checker"] * 2


@patch("agents.base.build_llm")
def test_judgment_is_populated_from_judge_output(mock_build):
    raw = '{"accuracy": 8, "balance": 7, "depth": 6, "reasoning_quality": 9, "winner": "proponent", "verdict": "ok"}'
    mock_build.return_value = _llm(raw)
    from orchestrator.graph import run_debate

    state = run_debate("AI", rounds=1)
    assert state["winner"] == "proponent"
    assert state["votes"]["accuracy"] == 8
    assert state["verdict"] == "ok"


@patch("agents.base.build_llm")
def test_provider_error_propagates(mock_build):
    llm = MagicMock()
    llm.invoke.side_effect = RuntimeError("AuthenticationError")
    mock_build.return_value = llm
    from orchestrator.graph import run_debate

    import pytest

    with pytest.raises(RuntimeError):
        run_debate("AI", rounds=1)
