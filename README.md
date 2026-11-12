<div align="center">

<h1>Multi-Agent Customer Support</h1>

<p><b>A router reads every customer message and hands it to the specialist built for that job: orders, refunds, FAQs or a human.</b></p>

<p>
  <a href="https://github.com/saqib-n/multi-agent-customer-support/actions/workflows/tests.yml"><img src="https://github.com/saqib-n/multi-agent-customer-support/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white" alt="Python: 3.12+">
  <img src="https://img.shields.io/badge/LangGraph-1.x-1C3C3C" alt="LangGraph: 1.x">
  <img src="https://img.shields.io/badge/models-OpenAI%20%7C%20Claude%20%7C%20Gemini-444444" alt="models: OpenAI | Claude | Gemini">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2E7D32" alt="license: MIT"></a>
</p>

<p>
  <a href="#what-it-does">What it does</a> &nbsp;|&nbsp;
  <a href="#how-it-works">How it works</a> &nbsp;|&nbsp;
  <a href="#sample-run">Sample run</a> &nbsp;|&nbsp;
  <a href="#quick-start">Quick start</a> &nbsp;|&nbsp;
  <a href="#configuration">Configuration</a> &nbsp;|&nbsp;
  <a href="#roadmap">Roadmap</a>
</p>

</div>

<br>

<h2>See it in action</h2>

<p align="center"><img src="demo/demo.gif" alt="Terminal recording of Multi-Agent Customer Support running on Google Gemini" width="100%"></p>

<p align="center"><sub>Recorded from a real run on Google Gemini (<code>gemini-3.1-flash-lite</code>) on 12 November 2026. Nothing is edited or scripted. Only the waiting time while the model thinks is shortened. <a href="demo/demo.mp4">Download the MP4</a>.</sub></p>

<h2>The problem</h2>

<p>One big support prompt handles simple questions fine and falls apart on refunds. It invents a policy, approves something it shouldn't, and never tells you it wasn't sure.</p>

<p>Businesses need an assistant that is helpful on routine questions and strict where money or policy is involved.</p>

<h2>What it does</h2>

<table>
  <tr><th align="left">Capability</th><th align="left">What that means in practice</th></tr>
  <tr><td><b>Smart routing</b></td><td>A classifier agent reads each message and sends it to the right specialist.</td></tr>
  <tr><td><b>Order lookup</b></td><td>Finds the order and gives its status and expected delivery.</td></tr>
  <tr><td><b>Refunds enforced in code</b></td><td>The order must be shipped or delivered and inside the 30-day window. Plain Python decides this, and the model can't overrule it.</td></tr>
  <tr><td><b>FAQ answers</b></td><td>Pulled from the knowledge base, not written from memory.</td></tr>
  <tr><td><b>Human handoff</b></td><td>Anything unclear or emotional opens a ticket and says so honestly.</td></tr>
  <tr><td><b>Conversation memory</b></td><td>An order number given in one message is still known three messages later.</td></tr>
</table>

<h2>How it works</h2>

<pre>
                       +----------------+
   customer message --&gt;|     Router     |
                       |  (classifier)  |
                       +-------+--------+
                               |
         +----------+----------+-----------+---------------+
         v          v                      v               v
   order_status   refund                  faq        human_handoff
   looks up the   checks the policy    searches the   opens a ticket
   order          before approving     knowledge base
</pre>

<p>The graph is built with LangGraph. The router uses the model only to choose a category. Each specialist calls tools in <code>agents/tools.py</code> that read the order data and apply the business rules.</p>

<p>Each conversation has a <code>thread_id</code>, and LangGraph's checkpointer keeps the state, so follow-up questions work without repeating details.</p>

<h2>Decisions I made on purpose</h2>

<h3>The model phrases the answer, it doesn't make the decision</h3>

<p>The refund rule is ordinary Python: the order status must be Delivered or Shipped, and the order must be under 30 days old. The agent explains the outcome but doesn't get a vote on whether a refund is allowed. That is the difference between a demo and something a business can trust with money.</p>

<h3>Escalate instead of refusing</h3>

<p>When a refund is outside the window, the agent doesn't refuse flatly and doesn't give in. It explains the rule and passes the case to a person in case an exception applies.</p>

<h2>Sample run</h2>

<p>The refund answer below is from a real run on Google Gemini:</p>

<pre>
$ python app.py
You: Where is my order ORD-1001?
Agent [order_status]: Order ORD-1001 (Wireless Earbuds Pro) is currently Shipped.
Estimated delivery: &lt;four days from today&gt;.

You: I want to return order ORD-1004
Agent [refund]: Order ORD-1004 was placed 68 days ago, which is outside our
30-day refund window. I'll escalate this to a human agent in case an exception applies.
</pre>

<h2>Quick start</h2>

<p>You need Python 3.12 or newer and an API key from OpenAI, Anthropic or Google Gemini.</p>

<pre>
pip install -r requirements.txt
cp .env.example .env        # on Windows: copy .env.example .env
# open .env and paste your API key
python app.py
</pre>

<p>Try an order question, a refund for ORD-1004, a policy question, and "I want to speak to a manager".</p>

<h2>Configuration</h2>

<p>Everything is set in <code>.env</code>. Copy <code>.env.example</code> to start.</p>

<table>
  <tr><th align="left">Variable</th><th align="left">Required</th><th align="left">Purpose</th></tr>
  <tr><td><code>LLM_MODEL</code></td><td>Yes</td><td>Which model to use, as <code>provider:model</code>. Default <code>openai:gpt-5.5</code>. Also works with <code>anthropic:claude-opus-5-5</code> or <code>google_genai:gemini-3.5-flash</code>.</td></tr>
  <tr><td><code>OPENAI_API_KEY / ANTHROPIC_API_KEY / GOOGLE_API_KEY</code></td><td>One of them</td><td>The key for whichever provider you picked.</td></tr>
</table>

<h2>Project structure</h2>

<pre>
multi-agent-customer-support/
  .env.example                                           # copy to .env and add your key
  app.py                                                 # chat in the terminal
  case_study.md                                          # longer write-up of the design
  README.md
  requirements.txt                                       # dependencies
  .git/
    COMMIT_EDITMSG
    config
    description
    HEAD
    hooks/applypatch-msg.sample
    hooks/commit-msg.sample
    hooks/fsmonitor-watchman.sample
    hooks/post-update.sample
    hooks/pre-applypatch.sample
    hooks/pre-commit.sample
    hooks/pre-merge-commit.sample
    hooks/pre-push.sample
    hooks/pre-rebase.sample
    hooks/pre-receive.sample
    hooks/prepare-commit-msg.sample
    hooks/push-to-checkout.sample
    hooks/sendemail-validate.sample
    hooks/update.sample
    index
    info/exclude
    logs/HEAD
    logs/refs/heads/main
    logs/refs/remotes/origin/main
    objects/01/e2803123fc1d58f93cc5b02dc85dc98ad9879e
    objects/0d/19a37d674a332b9dba9f34ec54f3144a81a21f
    objects/45/7c8ce56f517ebdad911e6286fa135a76151f61
    objects/47/feccf9261e65a184bdce3629d8d950d38685f2
    objects/63/d71b904df61169c3e320c87c6aac92e2460ab7
    objects/65/36a1ae1a6b7092204987ec5dcaf4591c90e15f
    objects/6f/b2ba3a772da32949e2b0851c5e24a51af803ac
    objects/78/998da0758f803a8b7d9b492206632524003f81
    objects/7a/3a4f0ab20b8170a7b714479283340f5fe09e10
    objects/88/eb69f5f363519d2259efbf4d3f8f6aa9eea56a
    objects/92/0de625bd9c58c8ca4912df832e620770a68a00
    objects/a2/2992dd5a497d81f2c4d52d29bebebfab28c81d
    objects/a2/667477f906e25e4d46862b73a0cf1d10163a78
    objects/a9/80b77401b076f1b89af7052c4995e63b3b56f0
    objects/b2/53cf884c281ae560ff955b113152002efbe7f1
    objects/bb/1d0d20270c6b562a687dd6c5e21f3c4d7ba090
    objects/c5/4aeb32cf364cf433dfb7c8ce58583bc231b3a2
    objects/c5/97c23fa30e7a1e2dfac8278bb520f879e325c9
    objects/cf/3936dd83f71ce6b12189d251f6b56aa0334be8
    objects/d3/095186de9672ac3e591fe3047e88f3a675742c
    objects/d9/d96ca41d7eca2cf4ba8d0762daa2a473441437
    objects/e5/6d0464232e3f00c54b6317bcda0a87126ef783
    objects/e6/9de29bb2d1d6434b8b29ae775ad8c2e48c5391
    objects/e7/971bfe341cb3b4763a5baae5da49675f9a3df5
    objects/ef/a866e10882b97fdead97719566e2fb26ed52a8
    refs/heads/main
    refs/remotes/origin/main
  agents/
    llm.py                                               # picks the model from LLM_MODEL
    support_graph.py                                     # router, specialists and memory
    tools.py                                             # order lookup, refund rules, FAQ search, tickets
  data/
    faq.json                                             # knowledge base
    orders.json                                          # demo orders
  demo/
    demo.gif
    demo.mp4
  tests/                                                 # pytest suite, runs without any API key
</pre>

<h2>Built with</h2>

<p>Python &nbsp;&middot;&nbsp; LangGraph &nbsp;&middot;&nbsp; LangChain &nbsp;&middot;&nbsp; OpenAI / Anthropic / Gemini</p>

<h2>Tests</h2>

<pre>
pip install -r requirements-dev.txt
pytest
</pre>

<p>Four tests cover all four outcomes of the refund rule, the FAQ search, the routing, and memory carrying an order ID across messages. None of the tests call a model or need an API key, so they run on GitHub Actions on every push. The badge at the top shows the latest result.</p>

<h2>Roadmap</h2>

<p>What I would build next if a client took this into production:</p>
<ul>
  <li>Point the tools at a real Shopify, Zendesk or Gorgias account. The graph doesn't change.</li>
  <li>A vector store for the FAQ instead of keyword matching</li>
  <li>Human approval for large refunds with a LangGraph interrupt</li>
  <li>Website chat widget, WhatsApp or email as the front end</li>
</ul>

<h2>More from this series</h2>

<p>Nine production-minded AI agents, each solving one business problem properly.</p>

<table>
  <tr><td><a href="https://github.com/saqib-n/ai-research-report-agent"><b>Research Report Agent</b></a></td><td>Researches a topic, notices its own gaps, and writes a report with a source for every claim.</td></tr>
  <tr><td><a href="https://github.com/saqib-n/ai-sales-outreach-agent"><b>AI Sales Outreach Agent</b></a></td><td>Personalised cold emails and follow-ups, with a human approving every send.</td></tr>
  <tr><td><a href="https://github.com/saqib-n/ecommerce-automation-agent"><b>E-commerce Order and Inventory Agent</b></a></td><td>Shopify order, stock and returns assistant, plus a monitor that warns you before stock runs out.</td></tr>
  <tr><td><a href="https://github.com/saqib-n/email-triage-agent"><b>Email Triage Agent</b></a></td><td>Sorts an inbox into four buckets and gives each one a different level of autonomy.</td></tr>
  <tr><td><a href="https://github.com/saqib-n/lead-qualification-crm-agent"><b>Lead Qualification Agent</b></a></td><td>Scores inbound leads against your own rubric and pushes the good ones to HubSpot.</td></tr>
  <tr><td><a href="https://github.com/saqib-n/rag-knowledge-base-agent"><b>RAG Knowledge Base Agent</b></a></td><td>Answers questions from your own documents and names the source for every answer.</td></tr>
  <tr><td><a href="https://github.com/saqib-n/recruiting-screening-agent"><b>Resume Screening Agent</b></a></td><td>Ranks resumes against a job description with evidence, and guards against common bias.</td></tr>
  <tr><td><a href="https://github.com/saqib-n/whatsapp-support-agent"><b>WhatsApp Support Agent</b></a></td><td>A WhatsApp Cloud API agent that checks orders, answers FAQs and escalates to a person.</td></tr>
</table>

<h2>Work with me</h2>

<p>I'm Saqib Nawaz, founder of WolfXense AI. I build AI agents and automations for businesses, with Python, LangChain, LangGraph and n8n, and connect them to the tools teams already use, like CRMs, Shopify, Slack, email and WhatsApp.</p>

<p>If you want an AI support assistant that follows your policies to the letter, I can connect this design to your order system and your help desk.</p>

<p><a href="https://www.upwork.com/freelancers/~01de008504a38baf28"><b>Hire me on Upwork</b></a> &nbsp;|&nbsp; <a href="https://github.com/saqib-n"><b>More of my work on GitHub</b></a></p>

<hr>

<p><sub>Released under the <a href="LICENSE">MIT License</a>. A longer write-up of the design is in <a href="case_study.md">case_study.md</a>.</sub></p>
