import time
from datetime import datetime

import josie_agents.utils.log as log
from josie_agents.tools.builtin.memory_tool import MemoryTool


class MemoryTypesDeepDive:
    """四种记忆类型深度解析演示类"""

    def __init__(self):
        self.setup_memory_systems()

    def setup_memory_systems(self):
        """设置不同的记忆系统"""
        log.delimiter("🧠 四种记忆类型深度解析")
        log.delimiter("=" * 60)

        # 创建专门的记忆工具实例
        self.working_memory_tool = MemoryTool(
            user_id="working_memory_user",
            memory_types=["working"]
        )

        self.episodic_memory_tool = MemoryTool(
            user_id="episodic_memory_user",
            memory_types=["episodic"]
        )

        self.semantic_memory_tool = MemoryTool(
            user_id="semantic_memory_user",
            memory_types=["semantic"]
        )

        self.perceptual_memory_tool = MemoryTool(
            user_id="perceptual_memory_user",
            memory_types=["perceptual"]
        )

        log.test("✅ 四种记忆系统初始化完成")

    def test_working_memory(self):
        """演示工作记忆的特点"""
        log.delimiter(" 💭 工作记忆 (Working Memory) 深度解析")
        log.delimiter("-" * 60)

        log.test("🔍 工作记忆特点:")
        log.test("• ⚡ 访问速度极快（纯内存存储）")
        log.test("• 📏 容量有限（默认50条记忆）")
        log.test("• ⏰ 自动过期（TTL机制）")
        log.test("• 🔄 适合临时信息存储")

        # 演示容量限制
        log.test(f" 1. 容量限制演示:")
        log.test("添加大量临时记忆，观察容量管理...")

        for i in range(8):
            content = f"临时工作记忆 {i + 1}: 当前正在处理任务步骤 {i + 1}"
            result = self.working_memory_tool.run({"action": "add",
                                                   "content": content,
                                                   "memory_type": "working",
                                                   "importance": 0.3 + (i * 0.1),
                                                   "task_step": i + 1})
            log.test(f"  添加记忆 {i + 1}: {result}")

        # 检查当前状态
        stats = self.working_memory_tool.run({"action": "stats"})
        log.test(f"当前工作记忆状态: {stats}")

        # 演示TTL机制
        log.test(f" 2. TTL（生存时间）机制演示:")

        # 添加一些带时间戳的记忆
        current_time = datetime.now()

        # 模拟不同时间的记忆
        time_memories = [
            ("刚刚的想法", 0, 0.8),
            ("5分钟前的任务", 5, 0.6),
            ("10分钟前的提醒", 10, 0.4),
            ("很久以前的笔记", 30, 0.2)
        ]

        for content, minutes_ago, importance in time_memories:
            # 这里我们模拟时间差异
            result = self.working_memory_tool.run({"action": "add",
                                                   "content": content,
                                                   "memory_type": "working",
                                                   "importance": importance,
                                                   "simulated_age_minutes": minutes_ago})
            log.test(f"  添加记忆: {content} (模拟 {minutes_ago} 分钟前)")

        # 演示快速检索
        log.test(f" 3. 快速检索演示:")

        search_queries = ["任务", "想法", "提醒"]

        for query in search_queries:
            start_time = time.time()
            results = self.working_memory_tool.run({"action": "search",
                                                    "query": query,
                                                    "memory_type": "working",
                                                    "limit": 3})
            search_time = time.time() - start_time
            log.test(f"  查询 '{query}': {search_time:.4f}秒")
            log.test(f"    结果: {results[:100]}...")

        # 演示自动清理
        log.test(f" 4. 自动清理机制:")

        # 获取清理前的统计
        before_stats = self.working_memory_tool.run({"action": "stats"})
        log.test(f"清理前: {before_stats}")

        # 触发清理（通过遗忘低重要性记忆）
        forget_result = self.working_memory_tool.run({"action": "forget",
                                                      "strategy": "importance_based",
                                                      "threshold": 0.4})
        log.test(f"清理结果: {forget_result}")

        # 获取清理后的统计
        after_stats = self.working_memory_tool.run({"action": "stats"})
        log.test(f"清理后: {after_stats}")
