"""
CodebaseMaintainer - 代码库维护助手

完整的长程智能体实现，整合:
1. ContextBuilder - 上下文管理
2. NoteTool - 结构化笔记
3. TerminalTool - 即时文件访问
4. MemoryTool - 对话记忆

关键改进：使用 Agentic 方式，让 agent 自主决定使用哪些工具
"""
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from josie_agents.agents.josie_function_call_agent import JosieFunctionCallAgent
from josie_agents.context.builder import ContextBuilder, ContextConfig, ContextPacket
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
        self._tracked_tool_event_count = 0

        log.test(f"✅ 代码库维护助手已初始化: {project_name} (Agentic Mode)")
        log.test(f"📁 工作目录: {codebase_path}")
        log.test(f"🆔 会话ID: {self.session_id}")
        log.test(f"🔧 可用工具: {', '.join(self.tool_registry.list_tools())}")

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
        log.delimiter(f"👤 用户: {user_input}")

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

        log.delimiter(f"🤖 助手回答: {response}")

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

    def _track_tool_usage(self):
        """统计工具使用情况"""
        tool_events = getattr(self.agent, "tool_call_history", [])
        new_events = tool_events[self._tracked_tool_event_count:]

        for event in new_events:
            tool_name = event.get("tool_name")
            arguments = event.get("arguments") or {}
            success = event.get("success") is True

            self.stats["tool_calls"] += 1

            if tool_name == "terminal" and arguments.get("command"):
                self.stats["commands_executed"] += 1

            if tool_name == "note" and arguments.get("action") == "create" and success:
                self.stats["notes_created"] += 1
                if arguments.get("note_type") == "blocker":
                    self.stats["issues_found"] += 1

        self._tracked_tool_event_count = len(tool_events)

        log.info(
            f" [track_tool_usage] tool_calls = {self.stats['tool_calls']}, "
            f"commands_executed = {self.stats['commands_executed']}, "
            f"notes_created = {self.stats['notes_created']}, "
            f"issues_found = {self.stats['issues_found']}"
        )


    def _retrieve_relevant_notes(self, query: str, limit: int = 3) -> List[Dict]:
        """检索相关笔记"""
        try:
            # 优先检索 blocker
            blockers_raw = self.note_tool.run({
                "action": "list",
                "note_type": "blocker",
                "limit": 2
            })

            # 通用搜索
            search_results_raw = self.note_tool.run({
                "action": "search",
                "query": query,
                "limit": limit
            })

            log.debug(f" 👌[CodebaseMaintainer][_ensure_list_of_dicts] Input: \n\t blockers_raw={blockers_raw}\n\t search_results_raw={search_results_raw}")
            blockers = self._ensure_list_of_dicts(blockers_raw)
            search_results = self._ensure_list_of_dicts(search_results_raw)
            log.debug(f" 👌[CodebaseMaintainer][_ensure_list_of_dicts] Output: \n\t blockers={blockers}\n\t search_results={search_results}")

            # 合并并去重
            all_notes = {}
            for note in blockers + search_results:
                if not isinstance(note, dict):
                    continue
                note_id = (
                    note.get("note_id")
                    or note.get("id")
                    or note.get("uuid")
                    or note.get("title")
                    or str(hash(str(note)))
                )
                all_notes[note_id] = note
            return list(all_notes.values())[:limit]

        except Exception as e:
            log.error(f"[WARNING] 笔记检索失败: {e}")
            return []

    def _ensure_list_of_dicts(self, data) -> List[Dict]:
        """将 NoteTool 返回规范化为字典列表"""
        if data is None:
            return []
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                return []
        if isinstance(data, dict):
            # 兼容 {"items": [...]} 或单条记录
            if "items" in data and isinstance(data["items"], list):
                return [item for item in data["items"] if isinstance(item, dict)]
            return [data]
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    def _notes_to_packets(self, notes: List[Dict]) -> List[ContextPacket]:
        """将笔记转换为上下文包"""
        packets = []

        for note in notes:
            if not isinstance(note, dict):
                continue
            # 根据笔记类型设置不同的相关性分数
            relevance_map = {
                "blocker": 0.9,
                "action": 0.8,
                "task_state": 0.75,
                "conclusion": 0.7
            }

            note_type = note.get('type', 'general')
            relevance = relevance_map.get(note_type, 0.6)

            content = f"[笔记:{note.get('title', 'Untitled')}]\n类型: {note_type}\n\n{note.get('content', '')}"
            updated_at = note.get('updated_at')
            try:
                note_timestamp = datetime.fromisoformat(updated_at) if updated_at else datetime.now()
            except (ValueError, TypeError):
                note_timestamp = datetime.now()

            packets.append(ContextPacket(
                content=content,
                timestamp=note_timestamp,
                token_count=len(content) // 4,
                relevance_score=relevance,
                metadata={
                    "type": "note",
                    "note_type": note_type,
                    "note_id": note.get('note_id') or note.get('id')
                }
            ))

        return packets


    def _build_system_instructions(self, mode: str) -> str:
        """构建系统指令（Agentic 方式）"""
        base_instructions = self._build_base_system_prompt()

        mode_hints = {
            "explore": """
用户当前关注: 探索代码库

建议策略:
- 考虑使用 TerminalTool 了解代码结构（如 find, ls, tree）
- 查看关键文件（如 README, 主要模块）
- 将架构信息记录到笔记方便后续查阅
""",
            "analyze": """
用户当前关注: 分析代码质量

建议策略:
- 考虑使用 grep 查找潜在问题（TODO, FIXME, BUG）
- 分析代码复杂度和结构
- 将发现的问题记录为 blocker 或 action 笔记
""",
            "plan": """
用户当前关注: 任务规划

建议策略:
- 回顾历史笔记了解当前进度
- 基于已有信息制定行动计划
- 创建或更新 task_state 类型的笔记
""",
            "auto": """
用户当前关注: 自由对话

建议策略:
- 根据用户需求灵活决策
- 在需要时主动使用工具获取信息
- 不需要时可以直接回答
"""
        }

        return base_instructions + "\n" + mode_hints.get(mode, mode_hints["auto"])

    def _update_history(self, user_input: str, response: str):
        """更新对话历史"""
        self.conversation_history.append(
            Message(content=user_input, role="user", timestamp=datetime.now())
        )
        self.conversation_history.append(
            Message(content=response, role="assistant", timestamp=datetime.now())
        )

        # 限制历史长度(保留最近100轮对话)
        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-100:]

    # === 便捷方法 ===

    def explore(self, target: str = ".") -> str:
        """探索代码库（Agentic 方式）

        Agent 会自主决定使用哪些命令来探索代码库
        """
        return self.run(f"请探索 {target} 的代码结构，了解项目组织方式", mode="explore")

    def analyze(self, focus: str = "") -> str:
        """分析代码质量（Agentic 方式）

        Agent 会自主决定如何分析代码质量
        """
        query = f"请分析代码质量" + (f"，重点关注{focus}" if focus else "")
        return self.run(query, mode="analyze")

    def plan_next_steps(self) -> str:
        """规划下一步任务（Agentic 方式）

        Agent 会查看历史笔记并规划下一步
        """
        return self.run("根据我们之前的分析和当前进度，规划下一步任务", mode="plan")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        duration = (datetime.now() - self.stats["session_start"]).total_seconds()

        # 获取笔记摘要
        try:
            note_summary = self.note_tool.run({"action": "summary"})
        except:
            note_summary = {}

        return {
            "session_info": {
                "session_id": self.session_id,
                "project": self.project_name,
                "duration_seconds": duration
            },
            "activity": {
                "commands_executed": self.stats["commands_executed"],
                "notes_created": self.stats["notes_created"],
                "issues_found": self.stats["issues_found"]
            },
            "notes": note_summary
        }

    def generate_report(self, save_to_file: bool = True) -> Dict[str, Any]:
        """生成会话报告"""
        report = self.get_stats()

        if save_to_file:
            report_file = f"maintainer_report_{self.session_id}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            report["report_file"] = report_file
            log.success(f"📄 报告已保存: {report_file}")

        return report

    def execute_command(self, command: str) -> str:
        """执行终端命令"""
        result = self.terminal_tool.run({"command": command})
        self.stats["commands_executed"] += 1
        return result

    def create_note(
        self,
        title: str,
        content: str,
        note_type: str = "general",
        tags: List[str] = None
    ) -> str:
        """创建笔记"""
        result = self.note_tool.run({
            "action": "create",
            "title": title,
            "content": content,
            "note_type": note_type,
            "tags": tags or [self.project_name]
        })
        self.stats["notes_created"] += 1
        return result


def main():
    """主函数 - 演示 CodebaseMaintainer 的使用（Agentic 版本）

    在这个版本中：
    - Agent 自主决定使用哪些工具
    - 不预定义工作流
    - Agent 根据需求灵活探索代码库
    """
    log.delimiter("CodebaseMaintainer 演示（Agentic 版本）")

    # 初始化助手
    maintainer = CodebaseMaintainer(
        project_name="flask_app",
        codebase_path="./flask_app",
        llm=JosieLLM()
    )

    # 探索代码库（Agent 自主决定如何探索）
    #log.test("### 探索代码库（Agent 自主探索）###")
    #response = maintainer.explore(target=".")

    # 分析代码质量（Agent 自主决定分析方法）
    log.test("### 分析代码质量（Agent 自主分析）###")
    response = maintainer.analyze(focus="代码风格")

    # 规划下一步（Agent 基于历史信息规划）
    #log.test("### 规划下一步任务（Agent 自主规划）###")
    #response = maintainer.plan_next_steps()

    # 生成报告
    log.test("### 生成会话报告 ###")
    report = maintainer.generate_report()
    log.test(json.dumps(report, indent=2, ensure_ascii=False))

    log.success("演示完成!")

if __name__ == "__main__":
    main()
