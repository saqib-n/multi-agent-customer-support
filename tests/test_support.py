from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage

from agents import support_graph
from agents.tools import process_refund, search_faq


def test_refund_rule():
    assert process_refund("ORD-1002")["approved"] is True
    late = process_refund("ORD-1004")
    assert (late["reason"], late["days_since_order"]) == ("outside_30_day_window", 68)
    assert process_refund("ORD-1003")["reason"] == "order_not_yet_delivered"
    assert process_refund("ORD-0000")["reason"] == "order_not_found"


def test_faq_search():
    assert search_faq("what's your return policy")["found"] is True
    assert search_faq("do you sell gift cards")["found"] is False


def test_unknown_label_goes_to_a_human():
    llm = GenericFakeChatModel(messages=iter([AIMessage(content="Refund.")]))
    result = support_graph.classify_node({"messages": [HumanMessage(content="money back for ORD-1002")]}, llm)
    assert result == {"category": "refund", "order_id": "ORD-1002"}
    assert support_graph.route_after_classify({"category": "other"}) == "human_handoff"


def test_memory_keeps_the_order_id():
    llm = GenericFakeChatModel(messages=iter([AIMessage(content="order_status"), AIMessage(content="order_status")]))
    app = support_graph.build_graph(llm=llm)
    config = {"configurable": {"thread_id": "t1"}}
    app.invoke({"messages": [HumanMessage(content="my order is ORD-1001")]}, config=config)
    result = app.invoke({"messages": [HumanMessage(content="is it going to be late?")]}, config=config)
    reply = result["messages"][-1].text
    assert "ORD-1001" in reply and "**" not in reply
