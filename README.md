# LexiGPT – Agentic Legal Co-Pilot

LexiGPT is an offline-first legal assistant that combines a planner–executor agent loop, Retrieval-Augmented Generation (RAG), and document drafting utilities on top of a local Ollama deployment. The stack pairs a lightweight Flask API with a responsive HTML/JS client, and runs entirely on-device for privacy-conscious workflows.

## Core Capabilities

- **Conversational Legal Assistant** – multi-turn chat backed by Ollama (e.g., `llama3`) with persisted local history.
- **RAG Pipeline** – ChromaDB vector store bootstrapped from `data/combined.json` for grounded answers with inline citations.
- **Agentic Loop** – planner → executor → evaluator chain that can call tools such as file readers, regex extractors, RAG search, and document generation.
- **Document Drafting** – ready-to-use templates (NDA, employment offers, legal notices) rendered locally with structured inputs.
- **Offline + Private** – no cloud calls; all data, embeddings, and chat transcripts stay on disk.

## Project Structure

```
├── app.py                  # Flask application entrypoint
├── config.py               # Environment-driven configuration
├── routes/                 # API blueprints (chat, RAG, agent, docgen, history)
├── services/               # Ollama client, agent runtime, docgen, chat store
├── rag/                    # Vector DB + retriever helpers
├── utils/                  # Shared helpers and prompts
├── scripts/                # One-off utilities and maintenance scripts
├── frontend/               # HTML/CSS/JS chat interface
├── docs/                   # Project reports, guides, and demo scripts
├── data/                   # Local persistence, uploads, and seed corpus
├── generated/              # Generated documents
└── requirements.txt
```

## Getting Started

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) with a local model pulled (e.g., `ollama pull llama3`)
- `chromadb` dependencies (installed via `pip`)

### Setup

1. **Install dependencies**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **(Optional) Seed/verify the Chroma DB**
   ```bash
   python scripts/build_law_chromadb.py
   ```
   The retriever will auto-seed from `data/combined.json` if the persistent store is empty.
3. **Run the Flask API**
   ```bash
   python app.py
   ```
4. **Open the UI**
   - Serve `frontend/index.html` via any static server **or**
   - Open `frontend/index.html` directly and let the scripts speak to `http://localhost:5000` (CORS is enabled).

## API Highlights

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/chat` | POST | Main chat endpoint. Pass `{ message, session_id?, mode? }`; returns `{ response, session_id, context? }`. `mode="rag"` forces contextual answers. |
| `/api/rag-query` | POST | Direct access to the RAG pipeline. |
| `/api/chats` | GET/POST | List or create chat sessions. |
| `/api/chats/<id>` | GET | Retrieve a session (messages, title, timestamps). |
| `/api/agent/plan-run` | POST | Kicks off the planner → executor → evaluator loop with `{ goal }`. |
| `/api/docgen` | POST | Generate documents with `{ template, fields }`. Templates: `nda`, `employment_offer`, `legal_notice`. |

## Configuration

Environment variables (optional) in `config.py`:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_MODEL` | `llama3` | Model to run via Ollama |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama HTTP endpoint |
| `VECTOR_DB_DIR` | `rag/vectordb` | Persistent Chroma folder |
| `LEGAL_DATA_FILE` | `data/combined.json` | Seed corpus |
| `CHAT_HISTORY_FILE` | `data/chat_history.json` | Chat transcript store |

## Testing the Flow

1. **Regular Chat** – type any legal query; the backend auto-creates a session and persists it locally.
2. **RAG Mode** – call the `/api/chat` endpoint with `{"mode": "rag"}` to ensure the answer is grounded in the retrieved context.
3. **Smoke Test** – run `python scripts/smoke_test.py` after starting the Flask server.
4. **Document Drafts** – `POST /api/docgen`:
   ```json
   {
     "template": "nda",
     "fields": {
       "disclosing_party": "Acme Ltd.",
       "receiving_party": "Spark Labs",
       "purpose": "sharing product roadmap",
       "term": "24 months",
       "governing_law": "Laws of India"
     }
   }
   ```
5. **Planner Loop** – `POST /api/agent/plan-run` with `{ "goal": "Summarise Section 3 of the Motor Vehicles Act" }`.

## Troubleshooting

- **Ollama not reachable** – ensure `ollama serve` is running and the `OLLAMA_HOST` matches.
- **Empty RAG results** – check that `rag/vectordb` contains the persisted Chroma files or rerun `rag/chroma_init.py`.
- **Permission issues** – Windows users may need to run the terminal as Administrator when initializing Chroma for the first time.

Happy lawyering! 🧑‍⚖️💻
