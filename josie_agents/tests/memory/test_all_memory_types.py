import time
from datetime import datetime, timedelta

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
        now = datetime.now()

        # 模拟不同时间的记忆
        time_memories = [
            ("刚刚的想法", now - timedelta(minutes=1), 1.5),
            ("20分钟前的任务", now - timedelta(minutes=20), 1.5),
            ("1小时前的提醒", now - timedelta(hours=1), 1.5),
            ("4h以前的笔记", now - timedelta(hours=4), 1.5)
        ]

        for content, ts, importance in time_memories:
            # 这里我们模拟时间差异
            result = self.working_memory_tool.run({"action": "add",
                                                   "content": content,
                                                   "memory_type": "working",
                                                   "importance": importance,
                                                   "timestamp": ts})
            log.test(f"  添加记忆: {content} ")

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
            log.test(f"查询 【{query}】: 耗时{search_time:.4f}秒")
            log.test(f"结果: {results[:500]}...")

        # 演示自动清理
        log.test(f" 4. 自动清理机制:")

        # 获取清理前的统计
        before_stats = self.working_memory_tool.run({"action": "stats"})
        log.test(f"清理前: {before_stats}")

        # 触发清理（通过遗忘低重要性记忆）
        forget_result = self.working_memory_tool.run({"action": "forget",
                                                      "strategy": "importance_based",
                                                      "threshold": 0.8})
        log.test(f"清理结果: {forget_result}")

        # 获取清理后的统计
        after_stats = self.working_memory_tool.run({"action": "stats"})
        log.test(f"清理后: {after_stats}")

    def test_episodic_memory(self):
        """演示情景记忆的特点"""
        log.delimiter("📖 情景记忆 (Episodic Memory) 深度解析")
        log.delimiter("-" * 60)

        log.test("🔍 情景记忆特点:")
        log.test("• 📅 完整的时间序列记录")
        log.test("• 🎭 丰富的上下文信息")
        log.test("• 🔗 支持记忆链条构建")
        log.test("• 💾 持久化存储")

        # 演示完整事件记录
        log.test(f" 1. 完整事件记录演示:")
        log.test("-" * 60)

        # 模拟一个完整的学习会话
        learning_session = [
            {
                "content": "开始学习Python机器学习",
                "context": "学习开始",
                "location": "家里书房",
                "mood": "专注",
                "importance": 0.7
            },
            {
                "content": "学习了线性回归的数学原理",
                "context": "理论学习",
                "chapter": "第3章",
                "difficulty": "中等",
                "importance": 0.8
            },
            {
                "content": "实现了第一个线性回归模型",
                "context": "实践编程",
                "code_lines": 45,
                "bugs_fixed": 2,
                "importance": 0.9
            },
            {
                "content": "完成了课后练习题",
                "context": "练习巩固",
                "exercises_completed": 5,
                "accuracy": 0.8,
                "importance": 0.6
            },
            {
                "content": "总结今天的学习收获",
                "context": "学习总结",
                "key_concepts": ["线性回归", "梯度下降", "损失函数"],
                "importance": 0.8
            }
        ]

        session_id = f"learning_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        for i, event in enumerate(learning_session):
            result = self.episodic_memory_tool.run({"action": "add",
                                                    "content": event["content"],
                                                    "memory_type": "episodic",
                                                    "importance": event["importance"],
                                                    "session_id": session_id,
                                                    "sequence_number": i + 1,
                                                    **{k: v for k, v in event.items() if
                                                       k not in ["content", "importance"]}})
            log.test(f"  事件 {i + 1}: {result}")

        # 演示时间序列检索
        log.test(f" 2. 时间序列检索演示:")
        log.test("-" * 60)

        # 按时间顺序检索
        timeline_search = self.episodic_memory_tool.run({"action": "search",
                                                         "query": "学习",
                                                         "memory_type": "episodic",
                                                         "session_id": "hahaha",
                                                         "limit": 10})
        log.test(f"学习时间线: {timeline_search}")

        # 按会话检索
        session_search = self.episodic_memory_tool.run({"action": "search",
                                                        "query": "线性回归",
                                                        "memory_type": "episodic",
                                                        "limit": 5})
        log.test(f"会话内容: {session_search}")

        # 演示上下文丰富性
        log.test(f" 3. 上下文信息演示:")
        log.test("-" * 60)

        # 添加带有丰富上下文的记忆
        rich_context_memory = {
            "content": "参加了AI技术分享会",
            "event_type": "conference",
            "location": "北京国际会议中心",
            "speakers": ["张教授", "李博士", "王工程师"],
            "topics": ["深度学习", "自然语言处理", "计算机视觉"],
            "attendees_count": 200,
            "duration_hours": 6,
            "weather": "晴朗",
            "transportation": "地铁",
            "networking_contacts": 3,
            "key_insights": ["Transformer架构的演进", "多模态学习的前景"],
            "follow_up_actions": ["阅读推荐论文", "尝试新框架"],
            "satisfaction_rating": 9
        }

        context_result = self.episodic_memory_tool.run({"action": "add",
                                                        "content": rich_context_memory["content"],
                                                        "memory_type": "episodic",
                                                        "importance": 0.9,
                                                        **{k: v for k, v in rich_context_memory.items() if
                                                           k != "content"}})
        log.test(f"丰富上下文记忆: {context_result}")

        # 演示记忆链条
        log.test(f"4. 记忆链条构建:")
        log.test("-" * 60)

        # 创建相关联的记忆序列
        memory_chain = [
            ("看到一篇关于GPT的论文", "trigger", None),
            ("决定深入研究Transformer架构", "decision", "trigger"),
            ("下载并阅读Attention is All You Need论文", "action", "decision"),
            ("实现了简化版的自注意力机制", "implementation", "action"),
            ("在项目中应用了学到的知识", "application", "implementation")
        ]

        chain_memories = {}
        for content, chain_type, parent_type in memory_chain:
            parent_id = chain_memories.get(parent_type) if parent_type else None

            result = self.episodic_memory_tool.run({"action": "add",
                                                    "content": content,
                                                    "memory_type": "episodic",
                                                    "importance": 0.7,
                                                    "chain_type": chain_type,
                                                    "parent_memory": parent_id,
                                                    "chain_id": "gpt_learning_chain"})

            # 提取记忆ID（简化处理）
            memory_id = f"{chain_type}_memory"
            chain_memories[chain_type] = memory_id
            log.test(f"  链条记忆: {content} (类型: {chain_type})")

        # 检索整个链条
        chain_search = self.episodic_memory_tool.run({"action": "search",
                                                      "query": "GPT Transformer",
                                                      "memory_type": "episodic",
                                                      "limit": 8})
        log.test(f"记忆链条检索: {chain_search}")

    def cleanup(self):
        log.delimiter("清空全部记忆，清理测试环境")
        result = self.working_memory_tool.run({
            "action": "clear_all",
        })
        log.test(f"WorkingMemory:{result}")

        result = self.episodic_memory_tool.run({
            "action": "clear_all",
        })
        log.test(f"EpisodicMemory:{result}")

        result = self.semantic_memory_tool.run({
            "action": "clear_all",
        })
        log.test(f"SemanticMemory:{result}")

        result = self.perceptual_memory_tool.run({
            "action": "clear_all",
        })
        log.test(f"PerceptualMemory:{result}")


def main():
    demo = MemoryTypesDeepDive()

    # 前置清理环境
    demo.cleanup()

    #demo.test_working_memory()

    demo.test_episodic_memory()

    # 后置清理环境
    demo.cleanup()

if __name__ == "__main__":
    main()
