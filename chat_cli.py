"""Terminal chat with the multi-agent customer support system.

Run:
    python chat_cli.py

Type a message as if you were a customer. Try things like:
    - "Where is my order ORD-1001?"
    - "I want a refund for ORD-1004, it arrived damaged"
    - "What's your return policy?"
    - "I want to speak to a manager, this is ridiculous"
"""

import uuid

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from agents.support_graph import build_graph

load_dotenv()


def main():
    graph = build_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("Multi-Agent Customer Support, type 'exit' to quit\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue

        result = graph.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)
        reply = result["messages"][-1].text
        category = result.get("category", "?")
        print(f"Agent [{category}]: {reply}\n")


if __name__ == "__main__":
    main()
