"""Support desk screen for the multi-agent customer support system.

Opens a page in the browser with the customer chat on one side and the
agent graph on the other. Each message lights up the router, the
specialist it picked, and the backend tool that specialist called. Same
graph as chat_cli.py.

Run:
    python app.py
"""

import functools
import logging
import os
import threading
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from agents import support_graph
from agents.llm import DEFAULT_MODEL

load_dotenv()

logger = logging.getLogger("multi-agent-support")
app = FastAPI(title="Multi-Agent Customer Support")
WEB_DIR = Path(__file__).resolve().parent / "web"
SPECIALIST = {"order_status": "order_status", "refund": "refund", "faq": "faq", "other": "human_handoff"}

# Record every backend tool call a specialist makes during one request, so
# the screen can show what was looked up and what came back. The graph
# itself is unchanged, the tools are just wrapped where it calls them.
_calls = threading.local()


def _traced(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        result = fn(*args, **kwargs)
        log = getattr(_calls, "log", None)
        if log is not None:
            log.append({"tool": fn.__name__, "args": [*args, *kwargs.values()], "result": result})
        return result
    return wrapper


for _name in ("get_order_status", "process_refund", "search_faq", "create_support_ticket"):
    setattr(support_graph, _name, _traced(getattr(support_graph, _name)))

_graph = None


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=2000)


def support_turn(session_id: str, text: str) -> dict:
    global _graph
    if _graph is None:
        _graph = support_graph.build_graph()
    _calls.log = []
    try:
        config = {"configurable": {"thread_id": f"web-{session_id}"}}
        result = _graph.invoke({"messages": [HumanMessage(content=text)]}, config=config)
        category = result.get("category") or "other"
        return {
            "reply": result["messages"][-1].text,
            "category": category,
            "specialist": SPECIALIST.get(category, "human_handoff"),
            "order_id": result.get("order_id"),
            "tools": _calls.log,
        }
    finally:
        _calls.log = None


@app.get("/", include_in_schema=False)
def desk():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/info")
def info():
    return {"model": os.getenv("LLM_MODEL") or DEFAULT_MODEL}


@app.post("/api/chat")
def chat(request: ChatRequest):
    started = time.perf_counter()
    try:
        turn = support_turn(request.session_id, request.text.strip())
    except Exception as exc:
        logger.exception("Support chat failed")
        detail = str(exc).splitlines()[0][:200] if str(exc) else ""
        return JSONResponse(status_code=502, content={"error": f"The agents could not answer ({type(exc).__name__}: {detail})."})
    return {**turn, "seconds": round(time.perf_counter() - started, 1)}


if __name__ == "__main__":
    import webbrowser

    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    uvicorn.run(app, host="127.0.0.1", port=port)
