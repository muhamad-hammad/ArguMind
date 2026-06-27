---
title: ArguMind Backend
emoji: 🧠
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# ArguMind Backend

FastAPI service powering the ArguMind multi-agent debate engine.

## Endpoints

- `GET /health` — liveness check
- `GET /test-agent` — smoke test (requires `OPENAI_API_KEY` secret)
- `POST /debate` — run a debate. The LLM provider and API key are supplied by the
  client via the `X-LLM-Provider` and `X-LLM-Key` request headers, so no server-side
  key is required for normal use.

## Configuration

Server-side keys are optional and only needed for `/test-agent`. Set them as Space
**secrets** (Settings → Variables and secrets), e.g. `OPENAI_API_KEY`.
