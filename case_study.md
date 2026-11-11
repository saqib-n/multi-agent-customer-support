# Multi-Agent Customer Support System

## For the Upwork portfolio entry

Built a customer support system where a router agent reads each incoming message and hands it to a specialist: order lookup, refunds, FAQ, or human handoff. The refund path enforces real business rules in plain Python (order must be shipped or delivered, must be inside 30 days) and the model doesn't get to override that, it only phrases the answer. Conversation memory is kept per customer thread, so an order ID given in one message is still known three messages later. Built on LangGraph, provider-agnostic between OpenAI, Anthropic and Gemini via one config line, and designed to drop into a real order system by swapping a single tools file.

**Stack:** Python, LangGraph, LangChain, OpenAI / Anthropic / Gemini

---

## The thing clients usually ask for

"We want an AI chatbot for our support inbox."

What they actually need is rarely a chatbot. It's a routing problem with a chat interface on top. A single prompt does fine on "what's your return policy" and then falls over the first time someone asks for their money back, because now the model is improvising policy it has no business improvising.

## What I built instead

A router that classifies the message, then four specialists that each do one job:

- **Order status** queries the order system. No invented tracking numbers.
- **Refund** runs the policy check in code before the model says anything. If the order shipped 68 days ago, the answer is no, and the model's job is only to explain that politely and offer escalation.
- **FAQ** retrieves from a knowledge base rather than generating from memory.
- **Human handoff** opens a ticket for anything the other three shouldn't touch.

## The design decision worth defending

The refund rules are not in the prompt. They're in `agents/tools.py` as ordinary Python conditionals.

This matters because prompts drift, models get swapped, and "the AI approved a refund it shouldn't have" is a conversation nobody wants to have with a client. Putting the rule in code means the worst case is a badly worded rejection, not an unauthorised payout.

## Why LangGraph

Three reasons that came up in practice:

The routing is an explicit graph, so a client can look at a diagram and see exactly which path a message takes. That's much easier to sell than "trust the prompt".

Adding a fifth specialist doesn't touch the other four.

And it supports pausing a graph mid-run for human approval, which is exactly what you need when a client eventually says "fine, but anything over $500 comes to me first".

## Where it stops

Mock JSON stands in for a real order system. For a client that's the first swap, `get_order_status` points at Shopify or Zendesk and nothing else changes.

After that: a vector store for the FAQ instead of keyword matching, the human-approval interrupt on large refunds, and per-category logging so the client can see what share of tickets are resolving without a person.

## My part

Architecture, the full LangGraph implementation, all four specialists and their tools, and the policy logic.
