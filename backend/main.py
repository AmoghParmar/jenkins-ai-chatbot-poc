"""
FastAPI app - serves the /query streaming endpoint.
"""

import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.rag import stream_answer

app = FastAPI(title="Jenkins AI Chatbot PoC", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    page_context: str = ""
    history: list[dict] = []


@app.get("/health")
def health():
    return {"status": "ok", "service": "Jenkins AI Chatbot PoC"}


@app.post("/query")
async def query(req: QueryRequest):
    """Stream an AI response for the given Jenkins question."""

    async def generate():
        loop = asyncio.get_event_loop()
        # Run the synchronous generator in a thread to avoid blocking
        gen = stream_answer(req.query, req.page_context, req.history)
        for token in gen:
            yield token.encode("utf-8")
            await asyncio.sleep(0)  # yield control to event loop

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")
