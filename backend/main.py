import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import OpenAI

from agents.models import DebateTopic, DebateTranscript
from security import RateLimitMiddleware

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=True)

logger = logging.getLogger("argumind")

app = FastAPI()

app.add_middleware(RateLimitMiddleware, max_requests=60, window_seconds=60)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/test-agent")
def test_agent():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not set. Copy .env.example to .env and add your key.",
        )
    client = OpenAI(api_key=api_key)
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello"}],
        )
    except Exception as e:
        logger.exception("LLM test call failed")
        raise HTTPException(status_code=502, detail="Upstream LLM request failed.") from e
    text = completion.choices[0].message.content
    return {"response": text}


@app.post("/debate", response_model=DebateTranscript)
async def debate(body: DebateTopic, request: Request) -> DebateTranscript:
    provider = request.headers.get("X-LLM-Provider")
    api_key = request.headers.get("X-LLM-Key")

    from orchestrator.graph import run_debate
    try:
        final_state = run_debate(body.topic, body.rounds, provider=provider, api_key=api_key)
    except Exception as e:
        logger.exception("Debate run failed")
        raise HTTPException(status_code=502, detail="Debate execution failed.") from e
    from agents.models import AgentMessage
    messages = [AgentMessage(**m) for m in final_state["transcript"]]
    judgment = {
        "votes": final_state.get("votes", {}),
        "winner": final_state.get("winner", ""),
        "verdict": final_state.get("verdict", ""),
    }
    return DebateTranscript(topic=body.topic, messages=messages, judgment=judgment)
