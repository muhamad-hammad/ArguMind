from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def _fake_state(topic: str = "AI", rounds: int = 1) -> dict:
    return {
        "topic": topic,
        "rounds": rounds,
        "round": rounds + 1,
        "transcript": [
            {"role": "proponent", "content": "p", "round": 1},
            {"role": "critic", "content": "c", "round": 1},
            {"role": "analyst", "content": "a", "round": 1},
            {"role": "fact_checker", "content": "f", "round": 1},
        ],
        "votes": {"accuracy": 8, "balance": 7, "depth": 6, "reasoning_quality": 9},
        "winner": "proponent",
        "verdict": "strong case",
        "status": "done",
    }


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@patch("orchestrator.graph.run_debate")
def test_debate_returns_transcript_and_judgment(mock_run):
    mock_run.return_value = _fake_state("AI in courts")
    resp = client.post("/debate", json={"topic": "AI in courts", "rounds": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert data["topic"] == "AI in courts"
    assert [m["role"] for m in data["messages"]] == [
        "proponent",
        "critic",
        "analyst",
        "fact_checker",
    ]
    assert data["judgment"]["winner"] == "proponent"


@patch("orchestrator.graph.run_debate")
def test_debate_defaults_to_three_rounds(mock_run):
    mock_run.return_value = _fake_state()
    client.post("/debate", json={"topic": "AI"})
    args, _ = mock_run.call_args
    assert args[1] == 3


@patch("orchestrator.graph.run_debate")
def test_debate_forwards_provider_and_key_headers(mock_run):
    mock_run.return_value = _fake_state()
    client.post(
        "/debate",
        json={"topic": "AI", "rounds": 1},
        headers={"X-LLM-Provider": "groq", "X-LLM-Key": "secret"},
    )
    _, kwargs = mock_run.call_args
    assert kwargs["provider"] == "groq"
    assert kwargs["api_key"] == "secret"


def test_debate_missing_topic_returns_422():
    assert client.post("/debate", json={"rounds": 1}).status_code == 422


@patch("orchestrator.graph.run_debate")
def test_debate_provider_error_returns_502(mock_run):
    mock_run.side_effect = RuntimeError("AuthenticationError: bad key")
    resp = client.post("/debate", json={"topic": "AI", "rounds": 1})
    assert resp.status_code == 502
    # Error details are intentionally not echoed to clients (information leakage).
    assert resp.json()["detail"] == "Debate execution failed."
