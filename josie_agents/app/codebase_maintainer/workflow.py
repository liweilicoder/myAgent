"""
CodebaseMaintainer 三天工作流演示

完整展示长程智能体在三天内的工作流程:
- 第一天: 探索代码库（Agent 自主探索）
- 第二天: 分析代码质量（Agent 自主分析）
- 第三天: 规划重构任务（Agent 自主规划）
- 一周后: 检查进度

"""

import os
import json
import time

from dotenv import load_dotenv

from josie_agents.core.josie_llm import JosieLLM
from josie_agents.utils import log

load_dotenv()

import sys
sys.path.append('.')
from codebase_maintainer import CodebaseMaintainer


def day_1_exploration(maintainer):
    """第一天: 探索代码库（Agentic 方式）

    在这个阶段，我们只给 Agent 高层次的目标，
    Agent 会自主决定：
    - 使用哪些 shell 命令探索代码库
    - 查看哪些文件
    - 是否记录笔记
    """
    log.delimiter("第一天: 探索代码库（Agent 自主探索）")

    # 1. 初步探索 - Agent 自主决定如何探索
    log.test("### 1. 初步探索项目结构 ###")
    log.test("💡 提示：Agent 会自主决定使用哪些命令（如 find, ls, cat）\n")
    response = maintainer.explore()
    log.test(f"助手总结:{response}...")

    # 2. 深入分析某个模块 - Agent 自主决定分析方法
    log.test("### 2. 分析数据处理模块 ###")
    log.test("💡 提示：Agent 会自主决定如何分析这个文件")
    response = maintainer.run("请查看 data_processor.py 文件，分析其代码设计")
    log.test(f"助手总结:{response}...")

    # 模拟时间流逝
    time.sleep(5)


def day_2_analysis(maintainer):
    """第二天: 分析代码质量（Agentic 方式）

    Agent 会自主决定：
    - 使用什么方法分析代码质量（grep TODO? 统计行数? 检查复杂度?）
    - 是否需要创建笔记记录问题
    - 如何组织分析结果
    """
    log.delimiter("第二天: 分析代码质量（Agent 自主分析）")

    # 1. 整体质量分析 - Agent 自主决定分析方法
    log.test("### 1. 分析代码质量 ###")
    log.test("💡 提示：Agent 会自主决定如何分析（如 grep TODO, wc -l, 复杂度分析）")
    response = maintainer.analyze()
    log.test(f"助手总结:{response}...")

    # 2. 查看具体问题 - Agent 自主深入分析
    log.test("### 2. 分析 API 客户端代码 ###")
    log.test("💡 提示：Agent 会自主决定如何分析这个文件的质量")
    response = maintainer.run("请分析 api_client.py 的代码质量，特别是错误处理部分，给出改进建议")
    log.test(f"助手总结:{response}...")

    # 模拟时间流逝
    time.sleep(5)


def day_3_planning(maintainer):
    """第三天: 规划重构任务（Agentic 方式）

    Agent 会自主决定：
    - 回顾哪些历史笔记
    - 如何组织任务规划
    - 是否需要创建新的笔记
    - 如何安排优先级
    """
    log.delimiter("第三天: 规划重构任务（Agent 自主规划）")

    # 1. 回顾进度 - Agent 自主查看历史笔记并规划
    log.test("### 1. 回顾当前进度并规划下一步 ###")
    log.test("💡 提示：Agent 会自主查看历史笔记，分析当前进度，并制定计划")
    response = maintainer.plan_next_steps()
    log.test(f"助手总结:{response}...")

    # 2. 询问 Agent 创建详细计划（Agent 会自主决定是否使用 NoteTool）
    log.test("### 2. 让 Agent 创建详细的重构计划 ###")
    log.test("💡 提示：Agent 会自主决定如何创建和组织重构计划")
    response = maintainer.run(
        "请基于我们的分析，创建一个详细的本周重构计划。"
        "计划应该包括：目标、具体任务清单、时间安排和风险。"
        "请使用 NoteTool 创建一个 task_state 类型的笔记来记录这个计划。"
    )
    log.test(f"助手总结:{response}...")

    # 模拟时间流逝
    time.sleep(5)


def week_later_review(maintainer):
    """一周后: 检查进度"""

    log.delimiter("一周后: 检查进度")

    # 1. 查看笔记摘要
    log.test("### 1. 笔记摘要 ###")
    summary = maintainer.note_tool.run({"action": "summary"})
    log.test("📊 笔记摘要:")
    log.test(json.dumps(summary, indent=2, ensure_ascii=False))

    # 2. 生成完整报告
    log.test("### 2. 会话报告 ###")
    report = maintainer.generate_report()
    log.test(" 📄 会话报告:")
    log.test(json.dumps(report, indent=2, ensure_ascii=False))


def demonstrate_cross_session_continuity():
    """演示跨会话的连贯性"""
    log.delimiter("演示跨会话的连贯性")

    # 第一次会话
    log.test("### 第一次会话 (session_1) ###")
    maintainer_1 = CodebaseMaintainer(
        project_name="demo_codebase",
        # 实际使用的时候替换代码路径
        codebase_path="/Users/jesse/PythonProjects/myAgent/josie_agents/app/codebase_maintainer/flask_app",
        llm=JosieLLM()
    )

    # 创建一些笔记
    maintainer_1.create_note(
        title="代码质量问题",
        content="发现多处 TODO 注释需要实现，特别是数据验证和错误处理部分",
        note_type="blocker",
        tags=["quality", "urgent"]
    )

    stats_1 = maintainer_1.get_stats()
    log.test(f"会话1统计: {stats_1['activity']}")

    # 模拟会话结束
    time.sleep(1)

    # 第二次会话 (新的会话ID,但笔记被保留)
    log.test("### 第二次会话 (session_2) ###")
    maintainer_2 = CodebaseMaintainer(
        project_name="demo_codebase",  # 同一个项目
        # 实际使用的时候替换代码路径
        codebase_path="/Users/jesse/PythonProjects/myAgent/josie_agents/app/codebase_maintainer/flask_app",
        llm=JosieLLM()
    )

    # 检索之前的笔记
    response = maintainer_2.run(
        "我们之前发现了什么代码质量问题？现在应该优先处理哪些？"
    )
    log.test(f"助手回答:{response}...")

    stats_2 = maintainer_2.get_stats()
    log.test(f"会话2统计: {stats_2['activity']}")

    # 展示笔记摘要
    summary = maintainer_2.note_tool.run({"action": "summary"})
    log.test("📊 跨会话笔记摘要:")
    log.test(json.dumps(summary, indent=2, ensure_ascii=False))


def demonstrate_tool_synergy():
    """演示三大工具的协同（Agentic 方式）

    在这个演示中：
    - 我们不再手动调用工具
    - 而是让 Agent 自主决定使用哪些工具
    - Agent 会根据任务自动协同使用多个工具
    """

    log.delimiter("演示三大工具的协同（Agent 自主协调）")

    maintainer = CodebaseMaintainer(
        project_name="synergy_demo",
        # 实际使用的时候替换代码路径
        codebase_path="/Users/jesse/PythonProjects/myAgent/josie_agents/app/codebase_maintainer/flask_app",
        llm=JosieLLM()
    )

    response = maintainer.run(
        "请分析代码库中的所有 TODO 项，并将发现记录到笔记中。"
        "然后告诉我应该优先实现哪些功能。"
    )
    log.test(f"助手回答:{response}...")

    # 展示统计信息
    stats = maintainer.get_stats()
    log.test("📊 工具使用统计:")
    log.test(f"  - 执行的命令: {stats['activity']['commands_executed']}")
    log.test(f"  - 创建的笔记: {stats['activity']['notes_created']}")


def main():
    """主函数"""

    # 初始化助手
    # maintainer = CodebaseMaintainer(
    #     project_name="demo_codebase",
    #     # 实际使用的时候替换代码路径
    #     codebase_path="/Users/jesse/PythonProjects/myAgent/josie_agents/app/codebase_maintainer/flask_app",
    #     llm=JosieLLM()
    # )
    #
    # # 执行三天工作流
    # day_1_exploration(maintainer)
    # day_2_analysis(maintainer)
    # day_3_planning(maintainer)
    # week_later_review(maintainer)

    # 额外演示
    log.test("额外演示")

    demonstrate_cross_session_continuity()
    demonstrate_tool_synergy()

    log.success("完整演示结束!")


if __name__ == "__main__":
    main()
