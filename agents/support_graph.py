"""LangGraph multi-agent customer support system.

Architecture
------------
A router (classifier) agent reads the customer's message and decides which
specialist should handle it:

    Router --> Order Status Agent  --> END
           --> Refund Agent        --> END
           --> FAQ Agent           --> END
           --> Human Handoff       --> END

Conversation memory is kept per `thread_id` via LangGraph's checkpointer, so
the same graph handles multi-turn conversations (e.g. the customer gives
their order ID in a follow-up message).
"""

import re
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from agents.llm import get_llm
from agents.tools import create_support_ticket, get_order_status, process_refund, search_faq

ORDER_ID_RE = re.compile(r"\bORD-\d{3,6}\b", re.IGNORECASE)


class SupportState(TypedDict):
    messages: Annotated[list, add_messages]
    category: str
    order_id: str | None


def classify_node(state: SupportState, llm) -> dict:
    last_user_msg = state["messages"][-1].content

    order_id_match = ORDER_ID_RE.search(last_user_msg)
    order_id = order_id_match.group(0).upper() if order_id_match else state.get("order_id")

    system = SystemMessage(content=(
        "You are a routing classifier for a customer support system. "
        "Classify the customer's latest message into exactly one category:\n"
        "- order_status: asking where an order is / delivery status\n"
        "- refund: asking for a refund, return, or money back\n"
        "- faq: general questions about policy, shipping, payment, tracking\n"
        "- other: anything you cannot confidently classify, complaints, "
        "or requests to speak to a human\n"
        "Reply with ONLY the single category word, nothing else."
    ))
    response = llm.invoke([system, *state["messages"]])
    category = response.text.strip().strip(".'\"").lower()
    if category not in {"order_status", "refund", "faq", "other"}:
        category = "other"

    return {"category": category, "order_id": order_id}


def order_status_node(state: SupportState) -> dict:
    order_id = state.get("order_id")
    if not order_id:
        reply = (
            "I can check that for you, could you share your order ID? "
            "It looks like ORD-1001."
        )
        return {"messages": [AIMessage(content=reply)]}

    result = get_order_status(order_id)
    if not result["found"]:
        reply = f"I couldn't find an order with ID {order_id}. Could you double-check it?"
    else:
        reply = (
            f"Order {result['order_id']} ({result['item']}) is currently "
            f"{result['status']}. Estimated delivery: {result['delivery_estimate']}."
        )
    return {"messages": [AIMessage(content=reply)]}


def refund_node(state: SupportState) -> dict:
    order_id = state.get("order_id")
    if not order_id:
        reply = "I can help with that refund, what's the order ID?"
        return {"messages": [AIMessage(content=reply)]}

    last_user_msg = state["messages"][-1].content
    result = process_refund(order_id, reason=last_user_msg)

    if result["approved"]:
        reply = (
            f"Your refund for order {result['order_id']} (${result['amount']:.2f}) "
            f"has been approved. Refund ticket: {result['refund_ticket']}. "
            "Funds will be returned to your original payment method within 5-7 business days."
        )
    elif result["reason"] == "order_not_found":
        reply = f"I couldn't find an order with ID {result['order_id']}."
    elif result["reason"] == "order_not_yet_delivered":
        reply = (
            f"Order {result['order_id']} is currently '{result['status']}' and hasn't "
            "been delivered yet, so a refund can't be processed until it arrives."
        )
    else:
        reply = (
            f"Order {result['order_id']} was placed {result['days_since_order']} days ago, "
            "which is outside our 30-day refund window. I'll escalate this to a human agent "
            "in case an exception applies."
        )
    return {"messages": [AIMessage(content=reply)]}


def faq_node(state: SupportState) -> dict:
    last_user_msg = state["messages"][-1].content
    result = search_faq(last_user_msg)
    if result["found"]:
        reply = result["answer"]
    else:
        reply = (
            "I don't have a direct answer for that in our FAQs. "
            "Let me connect you with a human agent."
        )
    return {"messages": [AIMessage(content=reply)]}


def human_handoff_node(state: SupportState) -> dict:
    last_user_msg = state["messages"][-1].content
    ticket = create_support_ticket(summary=last_user_msg)
    reply = (
        f"I've escalated this to our support team, ticket {ticket['ticket_id']} "
        "has been created and a human agent will follow up shortly."
    )
    return {"messages": [AIMessage(content=reply)]}


def route_after_classify(state: SupportState) -> Literal["order_status", "refund", "faq", "human_handoff"]:
    return {
        "order_status": "order_status",
        "refund": "refund",
        "faq": "faq",
        "other": "human_handoff",
    }[state["category"]]


def build_graph(model: str | None = None, llm=None):
    llm = llm or get_llm(model)

    graph = StateGraph(SupportState)
    graph.add_node("classify", lambda state: classify_node(state, llm))
    graph.add_node("order_status", order_status_node)
    graph.add_node("refund", refund_node)
    graph.add_node("faq", faq_node)
    graph.add_node("human_handoff", human_handoff_node)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges("classify", route_after_classify)
    graph.add_edge("order_status", END)
    graph.add_edge("refund", END)
    graph.add_edge("faq", END)
    graph.add_edge("human_handoff", END)

    return graph.compile(checkpointer=MemorySaver())
