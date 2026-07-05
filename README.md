# Knowledge Lens

A multi-agent orchestration system that breaks down complex questions into research, analysis, writing, and review — powered by LangGraph, LLMs, and semantic memory.

## Architecture

```
                 ┌──────────────┐
                 │   User Task  │
                 │ CLI / API    │
                 └──────┬───────┘
                        │
            ┌───────────▼───────────┐
            │     run_task()       │
            │  (graph.invoke)      │
            └───────────┬───────────┘
                        │
     ┌──────────────────▼──────────────────┐
     │         LangGraph Pipeline           │
     │                                      │
     │  plan ──→ research ──→ analyze       │
     │                    │                 │
     │                    ▼                 │
     │              write ←──── review      │
     │                 │        │           │
     │                 │   ┌────┴────┐     │
     │                 │ store rewrite │    │
     │                 │        │      │    │
     │                 └────────┘      │    │
     │                            human│    │
     │                           ┌──┴──┐    │
     │                        store  rewrite│
     └──────────────────────────────────────┘
```

### Agent Pipeline

| # | Agent | Role |
|---|-------|------|
| 1 | **Supervisor** | Queries ChromaDB for similar past tasks, then produces a JSON execution plan |
| 2 | **Researcher** | Runs DuckDuckGo web searches and synthesizes findings via LLM |
| 3 | **Analyst** | Extracts themes, patterns, caveats, and key takeaways from research |
| 4 | **Writer** | Generates a Markdown document from the analysis |
| 5 | **Reviewer** | Scores the document 1–10 on accuracy, completeness, clarity, and relevance |

### Conditional Flow

After review, the pipeline routes:
- **Score ≥ 7** → store result in memory → done
- **Score < 7 & iterations < 3** → rewrite with feedback
- **Score < 7 & iterations ≥ 3** → human approval gate:
  - **Approve** → store → done
  - **Feedback** → rewrite with user-provided feedback
  - **Reject** → store with rejection note → done

## Quick Start

### Prerequisites

- Python 3.10+
- API keys for at least one provider ([Groq](https://console.groq.com/keys) or [Gemini](https://aistudio.google.com/apikey))

### Installation

```bash
git clone https://github.com/Nikhilrai27/knowledge_lens.git
cd knowledge_lens
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` in the project root:

```env
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here
```

> Groq is the default provider (free and reliable). Gemini is used as a fallback.

### Streamlit UI (Recommended)

```bash
streamlit run streamlit_app.py
```

Opens a browser interface with a text input, provider selector, and rendered results.

### CLI Usage

```bash
# Run a single task
python main.py "Explain the difference between transformer and LSTM architectures"

# Interactive mode
python main.py --interactive

# Use Gemini provider
python main.py "What is quantum computing?" --provider gemini
```

### API Usage

```bash
uvicorn app:app --reload

# health check
curl http://localhost:8000/health

# run a task
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Explain attention mechanisms"}'
```

Returns:
```json
{
  "document": "# Attention Mechanisms\n\n...",
  "review_score": 8,
  "review_feedback": "Clear and comprehensive...",
  "iterations": 1
}
```

## Features

### LLM Providers

| Provider | Default Model | Library |
|----------|--------------|---------|
| **Groq** (default) | `llama-3.3-70b-versatile` | OpenAI-compatible client |
| **Gemini** | `gemini-2.5-flash` | `google-genai` |

### Semantic Memory

Results are stored in ChromaDB with `fastembed` (`all-MiniLM-L6-v2`) embeddings. Before planning a new task, the Supervisor queries the 3 most similar past results and injects them as context — enabling the system to learn from previous work.

Uses `fastembed` (ONNX-based) instead of `sentence-transformers` (PyTorch-based) to keep memory usage under 512MB for Render's free tier.

Storage is persistent on disk at `chroma_data/`.

### Tools

| Tool | Description |
|------|-------------|
| **Web Search** | DuckDuckGo search via `ddgs` — fetches up to 5 results with title/URL/snippet |
| **Calculator** | AST-safe arithmetic evaluator — supports `+`, `-`, `*`, `/`, `**`, `//`, `%` |

### Human Approval Gate

When the reviewer exhausts 3 rewrite cycles without passing, the pipeline pauses and presents:
- **(A)pprove** — accept the current document
- **(F)eedback** — provide revision instructions to the writer
- **(R)eject** — discard with a rejection note

## Deployment

### Render (free tier)

1. Push to GitHub
2. Go to [render.com](https://render.com) → **New+** → **Web Service**
3. Connect your repo
4. Use these settings (auto-detected from `render.yaml`):
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0`
5. Add env vars: `GEMINI_API_KEY`, `GROQ_API_KEY`

> Uses `fastembed` instead of `sentence-transformers` to keep memory within Render's 512MB free tier.

## Project Structure

```
knowledge_lens/
├── app.py                          # FastAPI entry point (API users)
├── main.py                         # CLI entry point
├── streamlit_app.py                # Streamlit UI entry point (default)
├── render.yaml                     # Render deployment config
├── requirements.txt
├── .env.example                    # Environment template
└── knowledge_lens/
    ├── cli.py                      # CLI logic + task runner
    ├── config.py                   # Environment loading
    ├── agents/
    │   ├── supervisor.py           # Task planning
    │   ├── researcher.py           # Web research
    │   ├── analyst.py              # Theme analysis
    │   ├── writer.py               # Document generation
    │   └── reviewer.py             # Quality scoring
    ├── graph/
    │   ├── state.py                # AgentState TypedDict
    │   └── workflow.py             # LangGraph StateGraph
    ├── llm/
    │   └── client.py               # Multi-provider LLM client
    ├── memory/
    │   └── semantic.py             # ChromaDB + fastembed memory
    ├── models/
    │   └── schemas.py              # Pydantic models
    └── tools/
        ├── calculator.py           # AST-safe calculator
        └── web_search.py           # DuckDuckGo search
```

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes* | — | Groq API key (default provider) |
| `GEMINI_API_KEY` | No | — | Gemini API key (fallback) |

\* At least one API key is required.

## Tech Stack

- **Orchestration**: [LangGraph](https://langchain-ai.github.io/langgraph/)
- **LLMs**: Groq (default), Gemini (fallback)
- **Memory**: ChromaDB + fastembed (ONNX)
- **Search**: DuckDuckGo (`ddgs`)
- **API**: FastAPI + Uvicorn
- **CLI**: Python argparse

## License

MIT
