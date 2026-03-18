# api.py — FastAPI for project_02_tool_agent
import json
from typing import List

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from loguru import logger

from agent import run, run_stream

app = FastAPI(title="Multi-Tool ReAct Agent API", version="1.0")


class ChatRequest(BaseModel):
    message: str
    chat_history: List[dict] = []


@app.post("/chat")
async def chat(req: ChatRequest):
    result = run(req.message)
    return result


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    def _gen():
        for event in run_stream(req.message):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream")


@app.get("/tools")
def list_tools():
    from agent import ALL_TOOLS
    return [{"name": t.name, "description": t.description} for t in ALL_TOOLS]


@app.get("/health")
def health():
    return {"status": "ok"}
