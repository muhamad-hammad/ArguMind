from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agents.base import build_llm
from agents.proponent import ProponentAgent
from agents.critic import CriticAgent
from agents.analyst import AnalystAgent
from agents.fact_checker import FactCheckerAgent
from agents.judge import JudgeAgent
from agents.models import AgentMessage


def _llm(content: str) -> MagicMock:
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content=content)
    return llm


@pytest.mark.parametrize(
    "agent_cls,role",
    [
        (ProponentAgent, "proponent"),
        (CriticAgent, "critic"),
        (AnalystAgent, "analyst"),
        (FactCheckerAgent, "fact_checker"),
    ],
)
def test_agent_respond_returns_llm_content(agent_cls, role):
    agent = agent_cls(_llm("hello"))
    assert agent.role == role
    assert agent.respond([], "topic") == "hello"


def test_respond_propagates_provider_error():
    llm = MagicMock()
    llm.invoke.side_effect = RuntimeError("AuthenticationError")
    with pytest.raises(RuntimeError):
        ProponentAgent(llm).respond([], "topic")


def test_respond_builds_system_history_and_prompt_messages():
    llm = _llm("ok")
    history = [
        AgentMessage(role="proponent", content="a", round=1),
        AgentMessage(role="critic", content="b", round=1),
    ]
    CriticAgent(llm).respond(history, "topic")
    sent = llm.invoke.call_args[0][0]
    assert len(sent) == len(history) + 2  # system + history + final prompt


def test_judge_parses_plain_json():
    raw = '{"accuracy": 8, "balance": 7, "depth": 6, "reasoning_quality": 9, "winner": "proponent", "verdict": "ok"}'
    result = JudgeAgent(_llm(raw)).judge([], "topic")
    assert result["winner"] == "proponent"
    assert result["accuracy"] == 8


def test_judge_strips_markdown_fence():
    raw = '```json\n{"accuracy": 5, "balance": 5, "depth": 5, "reasoning_quality": 5, "winner": "critic", "verdict": "x"}\n```'
    result = JudgeAgent(_llm(raw)).judge([], "topic")
    assert result["winner"] == "critic"


def test_judge_malformed_json_falls_back():
    result = JudgeAgent(_llm("not json")).judge([], "topic")
    assert result["winner"] == "unknown"
    assert "Judge fallback" in result["verdict"]


@pytest.mark.parametrize(
    "provider,expected_model",
    [
        ("openai", "gpt-4o-mini"),
        ("groq", "llama-3.1-8b-instant"),
        ("grok", "grok-3-mini"),
        ("openrouter", "meta-llama/llama-3.1-8b-instruct:free"),
    ],
)
def test_build_llm_selects_model_per_provider(provider, expected_model):
    llm = build_llm(provider, "test-key")
    assert llm.model_name == expected_model
