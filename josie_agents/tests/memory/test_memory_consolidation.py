import josie_agents.utils.log as log
from josie_agents.tools.builtin.memory_tool import MemoryTool

import time

class MemoryConsolidationDemo:
    def __init__(self):

        self.memory_tool = MemoryTool(
            user_id="consolidation_demo_user",
            memory_types=["working", "episodic", "semantic", "perceptual"]
        )
        log.test("✅ MemoryTool初始化完成")

    def setup_initial_memories(self):
        """设置初始记忆数据"""
        log.delimiter("📝 设置初始记忆数据")
        log.test("=" * 50)

        # 添加不同重要性的工作记忆
        working_memories = [
            {
                "content": "学习了Transformer架构的基本原理",
                "importance": 0.9,
                "topic": "deep_learning",
                "session": "study_session_1"
            },
            {
                "content": "完成了Python代码调试任务",
                "importance": 0.8,
                "topic": "programming",
                "task_type": "debugging"
            },
            {
                "content": "参加了团队会议讨论项目进展",
                "importance": 0.7,
                "topic": "teamwork",
                "meeting_type": "progress_review"
            },
            {
                "content": "查看了今天的天气预报",
                "importance": 0.3,
                "topic": "daily_life",
                "category": "routine"
            },
            {
                "content": "阅读了关于注意力机制的论文",
                "importance": 0.85,
                "topic": "research",
                "paper_type": "technical"
            },
            {
                "content": "喝了一杯咖啡",
                "importance": 0.2,
                "topic": "daily_life",
                "category": "routine"
            },
            {
                "content": "解决了一个复杂的算法问题",
                "importance": 0.9,
                "topic": "problem_solving",
                "difficulty": "high"
            },
            {
                "content": "整理了桌面文件",
                "importance": 0.4,
                "topic": "organization",
                "category": "maintenance"
            }
        ]

        log.test(" 添加工作记忆:")
        for i, memory in enumerate(working_memories):
            content = memory.pop("content")
            importance = memory.pop("importance")

            result = self.memory_tool.run({"action": "add",
                                           "content": content,
                                           "memory_type": "working",
                                           "importance": importance,
                                           **memory})

            log.test(f"  {i + 1}. {content[:40]}... (重要性: {importance})")

        log.test(f"✅ 已添加 {len(working_memories)} 条工作记忆")

        # 显示当前状态
        stats = self.memory_tool.run({"action": "stats"})
        log.test(f" 📊 当前记忆统计:\n{stats}")

    def demonstrate_consolidation_process(self):
        """演示实际的整合过程"""
        log.delimiter("🔄 记忆整合过程演示")
        log.test("-" * 50)

        log.test("整合过程步骤:")
        log.test("1. 筛选符合条件的记忆")
        log.test("2. 按重要性排序")
        log.test("3. 创建新的记忆项")
        log.test("4. 更新类型和元数据")
        log.test("5. 添加整合标记")

        # 执行不同阈值的整合
        consolidation_tests = [
            (0.6, "低阈值整合 - 整合更多记忆"),
            (0.8, "高阈值整合 - 只整合最重要的记忆")
        ]

        for threshold, description in consolidation_tests:
            log.test(f" 🔄 {description} (阈值: {threshold}):")

            # 获取整合前状态
            stats_before = self.memory_tool.run({"action": "stats"})
            log.test(f"整合前状态: {stats_before}")

            # 执行整合
            start_time = time.time()
            consolidation_result = self.memory_tool.run({"action": "consolidate",
                                                         "from_type": "working",
                                                         "to_type": "episodic",
                                                         "importance_threshold": threshold})
            consolidation_time = time.time() - start_time

            log.test(f"整合结果: {consolidation_result}")
            log.test(f"整合耗时: {consolidation_time:.3f}秒")

            # 获取整合后状态
            stats_after = self.memory_tool.run({"action": "stats"})
            log.test(f"整合后状态: {stats_after}")

            # 查看整合后的情景记忆
            log.test(f"📚 整合后的情景记忆:")
            episodic_search = self.memory_tool.run({"action": "search",
                                                    "query": "",
                                                    "memory_type": "episodic",
                                                    "limit": 5})
            log.test(episodic_search)

    def demonstrate_consolidation_metadata(self):
        """演示整合过程中的元数据处理"""
        log.delimiter("📋 整合元数据处理演示")
        log.test("-" * 50)

        log.test("元数据处理:")
        log.test("• 保留原始元数据")
        log.test("• 添加整合标记")
        log.test("• 记录整合时间")
        log.test("• 保存原始ID引用")

        # 添加一个特殊的工作记忆用于演示
        special_memory_result = self.memory_tool.run({"action": "add",
                                                      "content": "这是一个用于演示整合元数据处理的特殊记忆",
                                                      "memory_type": "working",
                                                      "importance": 0.85,
                                                      "special_tag": "metadata_demo",
                                                      "original_context": "demonstration",
                                                      "creation_purpose": "show_consolidation_metadata"
                                                      })

        log.test(f"添加特殊记忆: {special_memory_result}")

        # 执行整合
        log.test(f"🔄 执行整合...")
        consolidation_result = self.memory_tool.run({"action": "consolidate",
                                                     "from_type": "working",
                                                     "to_type": "episodic",
                                                     "importance_threshold": 0.8})

        log.test(f"整合结果: {consolidation_result}")

        # 搜索整合后的记忆查看元数据
        log.test(f"🔍 查看整合后的记忆元数据:")
        search_result = self.memory_tool.run({"action": "search",
                                              "query": "特殊记忆",
                                              "memory_type": "episodic",
                                              "limit": 1})
        log.test(f"【特殊记忆】的搜索结果：{search_result}")

    def demonstrate_multi_type_consolidation(self):
        """演示多类型记忆整合"""
        log.delimiter("🔀 多类型记忆整合演示")
        log.test("-" * 50)

        log.test("多类型整合场景:")
        log.test("• working → episodic (经历记录)")
        log.test("• working → semantic (知识提取)")
        log.test("• episodic → semantic (经验总结)")

        # 添加一些适合不同整合路径的记忆
        consolidation_candidates = [
            {
                "content": "学习了深度学习中的反向传播算法原理",
                "memory_type": "working",
                "importance": 0.9,
                "learning_type": "concept",
                "suitable_for": "semantic"
            },
            {
                "content": "今天下午参加了AI技术分享会",
                "memory_type": "working",
                "importance": 0.8,
                "event_type": "meeting",
                "suitable_for": "episodic"
            },
            {
                "content": "通过多次实践掌握了Transformer的实现技巧",
                "memory_type": "episodic",
                "importance": 0.85,
                "experience_type": "skill",
                "suitable_for": "semantic"
            }
        ]

        log.test(f" 📝 添加整合候选记忆:")
        for memory in consolidation_candidates:
            content = memory.pop("content")
            memory_type = memory.pop("memory_type")
            importance = memory.pop("importance")
            suitable_for = memory.pop("suitable_for")

            result = self.memory_tool.run({"action": "add",
                                           "content": content,
                                           "memory_type": memory_type,
                                           "importance": importance,
                                           **memory})

            log.test(f"  • {content[:50]}... → 适合整合为{suitable_for}")

        # 执行不同类型的整合
        consolidation_paths = [
            ("working", "episodic", 0.75, "经历记录整合"),
            ("working", "semantic", 0.85, "知识提取整合"),
            ("episodic", "semantic", 0.8, "经验总结整合")
        ]

        for from_type, to_type, threshold, description in consolidation_paths:
            log.test(f" 🔄 {description} ({from_type} → {to_type}):")

            result = self.memory_tool.run({"action": "consolidate",
                                           "from_type": from_type,
                                           "to_type": to_type,
                                           "importance_threshold": threshold})

            log.test(f"整合结果: {result}")

    def demonstrate_consolidation_benefits(self):
        """演示记忆整合的益处"""
        log.delimiter("✨ 记忆整合益处演示")
        log.test("-" * 50)

        log.test("整合益处:")
        log.test("• 长期保存重要信息")
        log.test("• 释放工作记忆空间")
        log.test("• 形成知识体系")
        log.test("• 提升检索效率")

        # 获取最终的记忆系统状态
        log.test(f" 📊 最终记忆系统状态:")
        final_stats = self.memory_tool.run({"action": "stats"})
        log.test(final_stats)

        # 获取各类型记忆的摘要
        log.test(f" 📋 各类型记忆摘要:")

        memory_types = ["working", "episodic", "semantic"]
        for memory_type in memory_types:
            log.test(f" {memory_type.upper()} 记忆:")
            type_summary = self.memory_tool.run({"action": "search",
                                                 "query": "",
                                                 "memory_type": memory_type,
                                                 "limit": 3})
            log.test(type_summary)

        # 演示整合后的检索效果
        log.test(f"🔍 整合后的检索效果测试:")
        search_queries = [
            ("深度学习", "测试跨类型检索"),
            ("学习经历", "测试整合记忆检索"),
            ("重要概念", "测试语义记忆检索")
        ]

        for query, description in search_queries:
            log.test(f" 查询: '{query}' ({description})")
            result = self.memory_tool.run({"action": "search",
                                           "query": query,
                                           "limit": 3})
            log.test(f"【{query}】的搜索结果：{result}")

    def cleanup(self):
        log.delimiter("清空全部记忆，清理测试环境")
        result = self.memory_tool.run({
            "action": "clear_all",
        })
        log.test(result)


def main():
    """主函数"""
    log.delimiter("🔄 记忆整合机制演示")
    log.test("展示从短期记忆到长期记忆的智能转化过程")
    log.test("=" * 60)

    try:
        demo = MemoryConsolidationDemo()

        demo.cleanup()

        # 1. 设置初始记忆数据
        demo.setup_initial_memories()

        # 3. 演示整合过程
        demo.demonstrate_consolidation_process()

        # 4. 演示元数据处理
        demo.demonstrate_consolidation_metadata()

        # 5. 演示多类型整合
        demo.demonstrate_multi_type_consolidation()

        # 6. 演示整合益处
        demo.demonstrate_consolidation_benefits()

        demo.cleanup()

        log.test("🎉 记忆整合机制演示完成！")
        log.test("=" * 60)


    except Exception as e:
        log.error(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()