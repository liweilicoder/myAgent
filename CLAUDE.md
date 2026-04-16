# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个旅行助手 Agent，基于 ReAct (Thought-Action-Observation) 模式实现，使用 MiniMax LLM 作为推理引擎。

## 架构

```
main.py                      # 入口，调用 agent.chat()
agent/simple_agent/
  agent_loop.py              # 核心循环：解析 LLM 输出、执行工具、构建 prompt history
  prompt.py                  # Agent system prompt (ReAct 格式要求)
  available_tools.py          # 工具注册表
agent/llm/llm.py             # OpenAI 兼容接口的 LLM 客户端
agent/tools/
  get_weather.py             # 通过 wttr.in 查询天气
  get_attraction.py          # 通过 Tavily Search 搜索景点
agent/logger.py              # 带颜色的日志工具
```

## 启动

```bash
source .venv/bin/activate
python main.py
```

## 环境变量 (.env)

- `MINIMAX_API_KEY` - MiniMax API 密钥
- `MINIMAX_BASE_URL` - MiniMax API 端点
- `MINIMAX_MODEL` - 模型名称
- `TAVILY_API_KEY` - Tavily Search API 密钥

## ReAct Agent 循环

`agent_loop.py` 实现了一个最多 8 轮的 ReAct 循环：
1. 调用 LLM，传入 prompt history
2. 解析 LLM 输出中的 `Thought:` 和 `Action:` 字段
3. 如 Action 是工具调用，执行工具并追加 `Observation:` 到 history
4. 如 Action 是 `Finish[答案]`，输出最终答案并结束
5. 截断多余的 Thought-Action 对，只保留最后一对

## 工具

- `get_weather(city)` - 无需 API key，使用 wttr.in
- `get_attraction(city, weather)` - 需要 `TAVILY_API_KEY`
