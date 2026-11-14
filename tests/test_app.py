from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

import app as web
from agents import support_graph


def test_desk_shows_route_and_tool_calls(monkeypatch):
    llm = GenericFakeChatModel(messages=iter([AIMessage(content="refund"), AIMessage(content="faq")]))
    monkeypatch.setattr(web, "_graph", support_graph.build_graph(llm=llm))
    client = TestClient(web.app)

    assert "Agent graph" in client.get("/").text

    refund = client.post("/api/chat", json={"session_id": "s1", "text": "refund ORD-1004 please"}).json()
    assert refund["specialist"] == "refund" and refund["order_id"] == "ORD-1004"
    assert refund["tools"][0]["tool"] == "process_refund"
    assert refund["tools"][0]["result"]["reason"] == "outside_30_day_window"

    faq = client.post("/api/chat", json={"session_id": "s1", "text": "what's your return policy"}).json()
    assert faq["specialist"] == "faq" and faq["tools"][0]["tool"] == "search_faq"
    assert faq["order_id"] == "ORD-1004"  # remembered from the first message
    assert client.post("/api/chat", json={"session_id": "s1", "text": ""}).status_code == 422
