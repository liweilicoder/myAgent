from datetime import datetime, timedelta

from josie_agents.tools.builtin.memory_tool import MemoryTool
import time
import josie_agents.utils.log as log


def test_memory_tool():
    memory_tool = MemoryTool(
        user_id="working_memory_demo",
        memory_types=["working"]  # 只启用工作记忆
    )

    """(1) 演示容量管理和TTL机制"""
    log.delimiter("🧠 工作记忆容量管理演示")
    log.delimiter("=" * 50)

    log.debug("工作记忆特点:")
    log.debug("• 容量有限（默认50条）")
    log.debug("• TTL机制（默认60分钟）")
    log.debug("• 自动清理过期记忆")
    log.debug("• 优先级管理（重要性排序）")

    # 添加多条记忆来演示容量管理
    log.info(f"📝 添加测试记忆...")
    for i in range(10):
        importance = 0.3 + (i * 0.07)  # 递增重要性
        memory_tool.run({
            "action": "add",
            "content": f"工作记忆测试项目 {i + 1} - 重要性 {importance:.2f}",
            "memory_type": "working",
            "importance": importance,
            "test_id": i + 1,
            "category": "capacity_test"
        })

    # 查看当前状态
    stats = memory_tool.run({"action": "stats"})
    log.info(f"当前状态: {stats}")

    # 演示重要性排序
    log.info(f"🔍 按重要性搜索:")
    result = memory_tool.run({
        "action": "search",
        "query": "测试项目",
        "memory_type": "working",
        "limit": 5
    })
    log.success(result)
    memory_tool.run({"action": "clear_all"})

    """(2) 演示混合检索策略"""
    log.delimiter("🔍 混合检索策略演示")
    log.delimiter("-" * 40)

    log.debug("混合检索策略包括:")
    log.debug("• TF-IDF向量化语义检索")
    log.debug("• 关键词匹配检索")
    log.debug("• 时间衰减因子")
    log.debug("• 重要性权重调整")

    # 添加不同类型的记忆用于检索测试
    test_memories = [
        {
            "content": "Python是一种高级编程语言，语法简洁清晰",
            "importance": 0.8,
            "topic": "programming",
            "language": "python"
        },
        {
            "content": "机器学习是人工智能的重要分支，包括监督学习和无监督学习",
            "importance": 0.9,
            "topic": "ai",
            "domain": "machine_learning"
        },
        {
            "content": "数据结构包括数组、链表、栈、队列等基本结构",
            "importance": 0.7,
            "topic": "computer_science",
            "category": "data_structures"
        },
        {
            "content": "算法复杂度分析使用大O记号来描述时间和空间复杂度",
            "importance": 0.8,
            "topic": "algorithms",
            "analysis": "complexity"
        }
    ]

    log.info(f"📝 添加测试记忆...")
    for i, memory in enumerate(test_memories):
        content = memory.pop("content")
        importance = memory.pop("importance")
        memory_tool.run({
            "action": "add",
            "content": content,
            "memory_type": "working",
            "importance": importance,
            **memory
        })

    # 测试不同类型的检索
    search_tests = [
        ("Python编程", "测试语义匹配"),
        ("学习", "测试关键词匹配"),
        ("复杂度", "测试部分匹配"),
        ("人工智能机器学习", "测试多词匹配")
    ]

    log.info(f"🔍 混合检索测试:")
    for query, description in search_tests:
        log.info(f"查询: '{query}' ({description})")
        result = memory_tool.run({
            "action": "search",
            "query": query,
            "memory_type": "working",
            "limit": 2
        })
        log.success(f"结果: {result}")
    memory_tool.run({"action": "clear_all"})

    """(3) 演示时间衰减机制"""
    log.delimiter("⏰ 时间衰减机制演示")
    log.delimiter("-" * 40)

    log.debug("时间衰减机制:")
    log.debug("• 新记忆权重更高")
    log.debug("• 旧记忆权重衰减")
    log.debug("• 模拟人类记忆特点")
    log.debug("• 平衡新旧信息重要性")

    # 工作记忆 TTL 默认 120 分钟，衰减公式 0.95^(hours/6)
    # 四条记忆分布在 0-110 分钟前，确保全部存活且衰减差异可见
    now = datetime.now()
    time_test_memories = [
        ("最新的重要信息 - 刚刚学习的概念（5分钟前）",  0.7, now - timedelta(minutes=5)),
        ("较新的信息 - 半小时前学习的内容（30分钟前）", 0.7, now - timedelta(minutes=30)),
        ("较旧的信息 - 一小时前学习的内容（70分钟前）", 0.7, now - timedelta(minutes=70)),
        ("最旧的信息 - 接近过期的内容（110分钟前）",    0.7, now - timedelta(minutes=110)),
    ]

    log.info(f"📝 添加不同时期的记忆...")
    for content, importance, ts in time_test_memories:
        memory_tool.run({
            "action": "add",
            "content": content,
            "memory_type": "working",
            "importance": importance,
            "timestamp": ts,
        })

    # 搜索测试时间衰减效果
    log.info(f"🔍 时间衰减效果测试:")
    result = memory_tool.run({
        "action": "search",
        "query": "学习的内容",
        "memory_type": "working",
        "limit": 4
    })
    log.success("搜索结果（注意时间因素对排序的影响）:")
    log.success(result)
    memory_tool.run({"action": "clear_all"})

    """(4)演示自动清理机制"""
    log.delimiter("🧹 自动清理机制演示")
    log.delimiter("-" * 40)

    log.debug("自动清理机制:")
    log.debug("• 过期记忆自动清理")
    log.debug("• 容量超限时清理低优先级记忆")
    log.debug("• 保持系统性能和响应速度")
    log.debug("• 模拟工作记忆的有限容量")

    # 添加一些低重要性的记忆
    log.info(f"📝 添加低重要性记忆...")
    for i in range(5):
        memory_tool.run({
            "action": "add",
            "content": f"低重要性临时记忆 {i + 1}",
            "memory_type": "working",
            "importance": 0.1 + i * 0.05,
            "temporary": True,
            "cleanup_test": True
        })

    # 获取清理前的状态
    stats_before = memory_tool.run({"action": "stats"})
    log.success(f"清理前状态: {stats_before}")

    # 触发基于重要性的清理
    log.info(f"🧹 执行基于重要性的清理...")
    cleanup_result = memory_tool.run({
        "action": "forget",
        "strategy": "importance_based",
        "threshold": 0.3
    })
    log.info(f"清理结果: {cleanup_result}")

    # 获取清理后的状态
    stats_after = memory_tool.run({"action": "stats"})
    log.success(f"清理后状态: {stats_after}")
    memory_tool.run({"action": "clear_all"})

    """(5) 演示性能特征"""
    log.delimiter("⚡ 性能特征演示")
    log.delimiter("-" * 40)

    log.debug("工作记忆性能特点:")
    log.debug("• 纯内存存储，访问速度极快")
    log.debug("• 无需磁盘I/O，响应时间短")
    log.debug("• 适合频繁访问的临时数据")
    log.debug("• 系统重启后数据丢失（符合设计）")

    # 性能测试
    log.info(f"⏱️ 性能测试:")

    # 批量添加测试
    start_time = time.time()
    for i in range(20):
        memory_tool.run({
            "action": "add",
            "content": f"性能测试记忆 {i + 1}",
            "memory_type": "working",
            "importance": 0.5,
            "performance_test": True
        })
    add_time = time.time() - start_time
    log.info(f"批量添加20条记忆耗时: {add_time:.3f}秒")

    # 批量搜索测试
    start_time = time.time()
    for i in range(10):
        memory_tool.run({
            "action": "search",
            "query": f"性能测试",
            "memory_type": "working",
            "limit": 3
        })
    search_time = time.time() - start_time
    log.info(f"批量搜索10次耗时: {search_time:.3f}秒")

    # 获取最终统计
    final_stats = memory_tool.run({"action": "stats"})
    log.success(f"\n📊 最终统计: {final_stats}")
    memory_tool.run({"action": "clear_all"})


if __name__ == "__main__":
    test_memory_tool()