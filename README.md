# myAgent

A travel assistant Agent based on [ReAct](https://react-lm.github.io/) (Thought-Action-Observation) pattern, powered by MiniMax LLM.

## Architecture

```
myAgent/
├── main.py                      # Entry point
├── agent/
│   ├── simple_agent/
│   │   ├── agent_loop.py        # Core ReAct loop
│   │   ├── prompt.py           # System prompt
│   │   └── available_tools.py  # Tool registry
│   ├── llm/
│   │   └── llm.py              # OpenAI-compatible LLM client
│   ├── tools/
│   │   ├── get_weather.py      # Weather via wttr.in
│   │   └── get_attraction.py   # Attractions via Tavily Search
│   └── logger.py               # Colored logging
└── website/                    # gitmoji.dev replica
```

## Setup

```bash
source .venv/bin/activate
python main.py
```

## Environment Variables (.env)

| Variable | Description |
|----------|-------------|
| `MINIMAX_API_KEY` | MiniMax API key |
| `MINIMAX_BASE_URL` | API endpoint |
| `MINIMAX_MODEL` | Model name |
| `TAVILY_API_KEY` | Tavily Search API key |

## ReAct Agent Loop

The agent runs up to 8 iterations:

1. Call LLM with prompt history
2. Parse `Thought:` and `Action:` from response
3. Execute tool if Action is a tool call, append `Observation:` to history
4. If Action is `Finish[answer]`, output final answer and exit
5. Truncate history, keeping only the last Thought-Action pair

## Tools

- `get_weather(city)` - Query weather (no API key required, uses wttr.in)
- `get_attraction(city, weather)` - Search attractions (requires `TAVILY_API_KEY`)
