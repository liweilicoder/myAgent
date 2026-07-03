"""
CodebaseMaintainer - 代码库维护助手

完整的长程智能体实现，整合:
1. ContextBuilder - 上下文管理
2. NoteTool - 结构化笔记
3. TerminalTool - 即时文件访问
4. MemoryTool - 对话记忆

关键改进：使用 Agentic 方式，让 agent 自主决定使用哪些工具
"""
from datetime import datetime
from typing import Optional, List

from josie_agents.agents.josie_function_call_agent import JosieFunctionCallAgent
from josie_agents.context.builder import ContextBuilder, ContextConfig
from josie_agents.core.josie_llm import JosieLLM
from josie_agents.core.message import Message
from josie_agents.tools.builtin.memory_tool import MemoryTool
from josie_agents.tools.builtin.note_tool import NoteTool
from josie_agents.tools.builtin.terminal_tool import TerminalTool
from josie_agents.tools.registry import ToolRegistry
from josie_agents.utils import log


class CodebaseMaintainer:
    """代码库维护助手 - 长程智能体示例

    整合 ContextBuilder + NoteTool + TerminalTool + MemoryTool
    实现跨会话的代码库维护任务管理

    核心特性：
    - Agent 自主使用工具探索代码库
    - 不预定义工作流，完全基于 agent 决策
    - 跨会话记忆和上下文管理
    """

    def __init__(
        self,
        project_name: str,
        codebase_path: str,
        llm: Optional[JosieLLM] = None
    ):
        self.project_name = project_name
        self.codebase_path = codebase_path
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 初始化 LLM
        self.llm = llm or JosieLLM()

        # 初始化工具
        self.memory_tool = MemoryTool(
            user_id=project_name,
            memory_types=["working"]
        )
        self.note_tool = NoteTool(workspace=f"./{project_name}_notes")
        self.terminal_tool = TerminalTool(workspace=codebase_path, timeout=60)

        # 初始化上下文构建器
        self.context_builder = ContextBuilder(
            memory_tool=self.memory_tool,
            rag_tool=None,  # 本案例不使用 RAG
            config=ContextConfig(
                max_tokens=4000,
                reserve_ratio=0.15,
                min_relevance=0.2,
                enable_compression=True
            )
        )

        # 创建工具注册表并注册工具
        self.tool_registry = ToolRegistry()
        self.tool_registry.register_tool(self.terminal_tool)
        self.tool_registry.register_tool(self.note_tool)
        self.tool_registry.register_tool(self.memory_tool)

        # 创建 Agent
        self.agent = JosieFunctionCallAgent(
            name="CodebaseMaintainer",
            llm=self.llm,
            system_prompt=self._build_base_system_prompt(),
            tool_registry=self.tool_registry,
            enable_tool_calling=True,
            max_tool_iterations=30
        )

        # 对话历史
        self.conversation_history: List[Message] = []

        # 统计信息
        self.stats = {
            "session_start": datetime.now(),
            "commands_executed": 0,
            "notes_created": 0,
            "issues_found": 0,
            "tool_calls": 0
        }

        log.success(f"✅ 代码库维护助手已初始化: {project_name} (Agentic Mode)")
        log.info(f"📁 工作目录: {codebase_path}")
        log.info(f"🆔 会话ID: {self.session_id}")
        log.info(f"🔧 可用工具: {', '.join(self.tool_registry.list_tools())}")

    def run(self, user_input: str, mode: str = "auto") -> str:
        """运行助手（Agentic 方式）

        Args:
            user_input: 用户输入
            mode: 运行模式提示（给 agent 提供方向性建议）
                - "auto": 自动决策是否使用工具
                - "explore": 建议 agent 侧重代码探索
                - "analyze": 建议 agent 侧重问题分析
                - "plan": 建议 agent 侧重任务规划

        Returns:
            str: 助手的回答
        """
        log.delimiter('=' * 80)
        log.delimiter(f"👤 用户: {user_input}")
        log.delimiter('=' * 80)

        # 第一步: 检索相关笔记（为 agent 提供上下文）
        relevant_notes = self._retrieve_relevant_notes(user_input)
        note_packets = self._notes_to_packets(relevant_notes)

        # 第二步: 构建优化的上下文
        context = self.context_builder.build(
            user_query=user_input,
            conversation_history=self.conversation_history,
            system_instructions=self._build_system_instructions(mode),
            additional_packets=note_packets
        )

        # 第三步: 让 Agent 自主决策和使用工具
        log.delimiter("🤖 Agent 正在思考并决定使用哪些工具...")

        # 更新 agent 的系统提示（包含上下文）
        self.agent.system_prompt = context

        # 调用 agent（agent 会自主决定是否使用工具）
        response = self.agent.run(user_input)

        # 第四步: 统计工具使用情况
        self._track_tool_usage()

        # 第五步: 更新对话历史
        self._update_history(user_input, response)

        log.delimiter(f"🤖 助手: {response}\n")
        log.delimiter('=' * 80)

        return response

    def _build_base_system_prompt(self) -> str:
        """构建基础系统提示"""
        return f"""你是 {self.project_name} 项目的代码库维护助手。

你的核心能力:
1. 使用 TerminalTool 探索代码库
   - 你可以执行任何 shell 命令: ls, cat, grep, find, git 等
   - 工作目录: {self.codebase_path}

2. 使用 NoteTool 记录发现和任务
   - 创建笔记记录重要发现
   - 笔记类型: blocker(阻塞问题)、action(行动计划)、task_state(任务状态)、conclusion(结论)

3. 使用 MemoryTool 存储关键信息
   - 记住重要的上下文信息
   - 跨会话保持连贯性

当前会话ID: {self.session_id}

重要原则:
- 你要自主决定使用哪些工具、执行什么命令
- 探索代码库时，先了解整体结构，再深入细节
- 发现重要信息时，主动使用 NoteTool 记录
- 保持回答的专业性和实用性
"""
