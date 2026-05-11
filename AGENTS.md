# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

A ReAct-pattern travel assistant agent using MiniMax LLM. See `README.md` and `CLAUDE.md` for architecture details.

### Required secrets (environment variables)

The agent requires four environment variables. Set them as Cursor Cloud secrets:

| Variable | Purpose |
|---|---|
| `MINIMAX_API_KEY` | MiniMax LLM API key |
| `MINIMAX_BASE_URL` | MiniMax API endpoint (e.g. `https://api.minimax.chat/v1`) |
| `MINIMAX_MODEL` | Model name (e.g. `MiniMax-Text-01`) |
| `TAVILY_API_KEY` | Tavily Search API key for attraction lookups |

### Running the agent

```bash
source .venv/bin/activate
python main.py
```

### Known gotcha: hardcoded `.env` path

`agent/simple_agent/agent_loop.py` and `agent/tools/get_attraction.py` both call `load_dotenv()` with a hardcoded macOS path (`/Users/jesse/PythonProjects/myAgent/.env`). This silently fails on Cloud VMs, so the agent relies on actual environment variables being exported in the shell. As long as secrets are configured in Cursor Cloud, `os.getenv()` picks them up correctly.

### Lint

```bash
source .venv/bin/activate
ruff check .
```

### Website (optional)

An unrelated gitmoji.dev replica lives in `website/`. Start with `python3 -m http.server 8084` from that directory.
