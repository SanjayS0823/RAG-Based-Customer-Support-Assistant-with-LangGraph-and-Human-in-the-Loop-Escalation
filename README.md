# RAG Internship Project: Customer Support Assistant (LangGraph + HITL)

This project implements a Retrieval-Augmented Generation (RAG) customer support assistant with:
- PDF knowledge-base ingestion
- Chunking + embeddings + ChromaDB storage
- Context retrieval for user queries
- LangGraph orchestration with intent-aware conditional routing
- Human-in-the-Loop (HITL) escalation and ticket resolution

## Project Structure

```
rag-internship-project/
├── data/
│   ├── chroma/                  # Chroma persistence directory
│   └── hitl_queue/              # Escalation tickets
├── deliverables/                # Generated PDFs
├── docs/
│   ├── HLD.md
│   ├── LLD.md
│   └── TECHNICAL_DOCUMENTATION.md
├── scripts/
│   ├── ingest_pdf.py
│   ├── chat_cli.py
│   ├── web_app.py
│   └── export_docs_to_pdf.py
├── static/
│   ├── app.css
│   ├── app.js
│   └── hitl.js
├── templates/
│   ├── index.html
│   └── hitl.html
├── samples/
│   └── customer_support_kb.md
├── src/rag_support/
│   ├── config.py
│   ├── embeddings.py
│   ├── graph.py
│   ├── hitl.py
│   ├── ingestion.py
│   ├── intents.py
│   ├── llm.py
│   ├── models.py
│   ├── retriever.py
│   └── web.py
├── .env.example
└── requirements.txt
```

## Setup

1. Create and activate a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Copy environment template.

```bash
cp .env.example .env
```

## Run the Assistant

1. Ingest your knowledge-base PDF.

```bash
PYTHONPATH=src python scripts/ingest_pdf.py --pdf /absolute/path/to/knowledge_base.pdf
```

2. Start chat assistant.

```bash
PYTHONPATH=src python scripts/chat_cli.py --user-id customer-001
```

3. Optional HITL commands inside CLI.

```text
/tickets
/resolve <ticket_id> <human_answer>
```

## Run the Web UI

Start the web app:

```bash
PYTHONPATH=src python scripts/web_app.py --host 127.0.0.1 --port 8000
```

Then visit:

```text
http://127.0.0.1:8000
```

HITL console:

```text
http://127.0.0.1:8000/hitl
```

Web features:
- Ask support questions and view intent/confidence/route
- See retrieved chunk sources
- View open HITL tickets on dedicated HITL page
- Resolve tickets with human responses from HITL page


## Notes

- The embedding layer uses a deterministic local hashing embedder for an offline-friendly setup.
- If `OPENAI_API_KEY` is set, the assistant uses OpenAI for answer generation; otherwise it uses a deterministic fallback generator.
- Conditional routing in LangGraph escalates to HITL based on intent, retrieval confidence, missing context, and query complexity.
