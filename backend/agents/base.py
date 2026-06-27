from __future__ import annotations

import os
from abc import ABC

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from .models import AgentMessage


def build_llm(provider: str | None = None, api_key: str | None = None) -> BaseChatModel:
    provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower()

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            google_api_key=api_key or os.getenv("GEMINI_API_KEY"),
        )

    from langchain_openai import ChatOpenAI

    if provider == "grok":
        return ChatOpenAI(
            model=os.getenv("GROK_MODEL", "grok-3-mini"),
            api_key=api_key or os.getenv("GROK_API_KEY"),
            base_url="https://api.x.ai/v1",
        )

    if provider == "groq":
        return ChatOpenAI(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            api_key=api_key or os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
        )

    if provider == "openrouter":
        return ChatOpenAI(
            model=os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"),
            api_key=api_key or os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )

    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=api_key or os.getenv("OPENAI_API_KEY"),
    )


class BaseAgent(ABC):
    role: str = ""
    system_prompt: str = ""

    def __init__(self, llm: BaseChatModel) -> None:
        self.llm = llm

    def respond(self, messages: list[AgentMessage], topic: str) -> str:
        chat: list = [SystemMessage(content=self.system_prompt)]

        for i, msg in enumerate(messages):
            if i % 2 == 0:
                chat.append(HumanMessage(content=msg.content))
            else:
                chat.append(AIMessage(content=msg.content))

        chat.append(
            HumanMessage(
                content=f"Topic: {topic}\n\nPlease give your response for this round."
            )
        )

        return self.llm.invoke(chat).content
