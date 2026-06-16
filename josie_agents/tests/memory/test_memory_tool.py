"""
    MemoryTool基础操作
    展示MemoryTool的核心execute方法和基本操作
"""

import josie_agents.utils.log as log
from josie_agents.tools.builtin.memory_tool import MemoryTool


def create_memory_tool():
    log.delimiter("🧠 MemoryTool基础操作演示")
    log.delimiter("=="*50)
    # 初始化MemoryTool
    memory_tool = MemoryTool(
        user_id="jesse",
        memory_types=["working", "episodic", "semantic", "perceptual"]
    )

    log.success("✅ MemoryTool初始化完成")
    return memory_tool


def test_add_memory(memory_tool):
    """添加记忆演示 - 模拟人类记忆编码过程"""
    log.delimiter("📝 添加记忆演示")
    log.delimiter("=="*50)

    # 添加工作记忆
    result = memory_tool.run({
        "action": "add",
        "content": "正在学习HelloAgents框架的记忆系统",
        "memory_type": "working",
        "importance": 0.7,
        "task_type": "learning"
    })
    log.info(f"工作记忆: {result}")

    # 添加情景记忆
    result = memory_tool.run({
        "action": "add",
        "content": "2024年开始深入研究AI Agent技术",
        "memory_type": "episodic",
        "importance": 0.8,
        "event_type": "milestone",
        "location": "研发中心"
    })
    log.info(f"情景记忆: {result}")

    # 添加语义记忆
    result = memory_tool.run({
        "action": "add",
        "content": "记忆系统包括工作记忆、情景记忆、语义记忆和感知记忆四种类型",
        "memory_type": "semantic",
        "importance": 0.9,
        "concept": "memory_types",
        "domain": "cognitive_science"
    })
    log.info(f"语义记忆: {result}")

    # 添加感知记忆
    result = memory_tool.run({
        "action": "add",
        "content": "查看了记忆系统的架构图和实现代码",
        "memory_type": "perceptual",
        "importance": 0.6,
        "modality": "text",
        "source": "technical_documentation"
    })
    log.info(f"感知记忆: {result}")


def test_search_memory(memory_tool):
    """搜索记忆演示 - 实现语义理解的检索"""
    log.delimiter("🔍 搜索记忆演示")
    log.delimiter("==" * 50)

    # 基础搜索
    log.info("基础搜索 - '记忆系统':")
    result = memory_tool.run({"action": "search", "query": "记忆系统", "limit": 3})
    log.debug(result)

    # 按类型搜索
    log.info("按类型搜索 - 语义记忆中的'记忆':")
    result = memory_tool.run({
        "action": "search",
        "query": "记忆",
        "memory_type": "semantic",
        "limit": 2
    })
    log.debug(result)

    # 设置重要性阈值
    log.info("高重要性记忆搜索:")
    result = memory_tool.run({
        "action": "search",
        "query": "AI Agent",
        "min_importance": 0.7,
        "limit": 3
    })
    log.debug(result)


def test_memory_summary(memory_tool):
    """记忆摘要演示 - 提供系统全貌"""
    log.delimiter("📋 记忆摘要演示")
    log.delimiter("=="*50)

    # 获取记忆摘要
    result = memory_tool.run({"action": "summary", "limit": 5})
    log.info("记忆摘要:")
    log.info(result)

    # 获取统计信息
    log.info("📊 统计信息:")
    result = memory_tool.run({"action": "stats"})
    log.info(result)


def test_memory_management(memory_tool):
    """记忆管理演示 - 遗忘和整合"""
    log.delimiter("⚙️ 记忆管理演示")
    log.delimiter("==" * 50)

    # 添加一个低重要性记忆用于遗忘测试
    memory_tool.run({
        "action": "add",
        "content": "这是一个临时的测试记忆，重要性很低",
        "memory_type": "working",
        "importance": 0.1
    })

    # 基于重要性的遗忘
    log.info("基于重要性的遗忘 (阈值=0.2):")
    result = memory_tool.run({
        "action": "forget",
        "strategy": "importance_based",
        "threshold": 0.2
    })
    log.info(result)

    # 记忆整合 - 将重要的工作记忆转为情景记忆
    log.info("记忆整合 (working → episodic):")
    result = memory_tool.run({
        "action": "consolidate",
        "from_type": "working",
        "to_type": "episodic",
        "importance_threshold": 0.6
    })
    log.info(result)

def test_clear_memory(memory_tool):
    log.delimiter("清空全部记忆， 清理测试环境")
    result = memory_tool.run({
        "action": "clear_all",
    })
    log.info(result)

if __name__ == "__main__":
    try:
        # 1. 初始化MemoryTool
        memory_tool = create_memory_tool()

        # 2. 添加记忆演示
        test_add_memory(memory_tool)

        # 3. 搜索记忆演示
        test_search_memory(memory_tool)

        # 4. 记忆摘要演示
        test_memory_summary(memory_tool)

        # 5. 记忆管理演示
        test_memory_management(memory_tool)

        test_clear_memory(memory_tool)

        log.success("🎉 MemoryTool基础操作演示完成！")

    except Exception as e:
        log.error(f"❌ 演示过程中发生错误: {e}")
        import traceback

        traceback.print_exc()

