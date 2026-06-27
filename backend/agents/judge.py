from __future__ import annotations

import json

from langchain_core.messages import SystemMessage, HumanMessage

from .base import BaseAgent
from .models import AgentMessage

_SYSTEM_PROMPT = """\
You are the Judge evaluating a structured debate.

Given a full debate transcript, score it on four dimensions (each 1–10):
- accuracy        : how factually grounded the arguments were
- balance         : how well both sides were represented
- depth           : how deeply the key issues were explored
- reasoning_quality : how logically sound the arguments were

Also pick a winner (proponent or critic) based on whose arguments were stronger overall,
and write a one-sentence verdict explaining your decision.

Return ONLY a valid JSON object with exactly these keys:
  accuracy, balance, depth, reasoning_quality, winner, verdict

Do not include any text outside the JSON object.\
"""


class JudgeAgent(BaseAgent):
    role = "judge"
    system_prompt = _SYSTEM_PROMPT

    def judge(self, messages: list[AgentMessage], topic: str) -> dict:
        transcript_lines = "\n".join(
            f"[Round {m.round}] {m.role.upper()}: {m.content}" for m in messages
        )

        chat = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=(
                    f"Topic: {topic}\n\n"
                    f"Transcript:\n{transcript_lines}\n\n"
                    "Now produce your JSON judgment."
                )
            ),
        ]

        raw = self.llm.invoke(chat).content.strip()
        # models often wrap JSON in a ```json ... ``` fence
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError as exc:
            return {
                "accuracy": 0,
                "balance": 0,
                "depth": 0,
                "reasoning_quality": 0,
                "winner": "unknown",
                "verdict": f"[Judge fallback] Could not parse LLM response as JSON: {exc}",
            }
