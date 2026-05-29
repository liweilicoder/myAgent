from dotenv import load_dotenv
from josie_agents.core.josie_llm import JosieLLM
from josie_agents.tools.registry import ToolRegistry
from josie_agents.tools.builtin.calculator import Calculator
from josie_agents.tools.builtin.advanced_search import AdvancedSearchTool
from josie_agents.agents.josie_react_agent import JosieReactAgent

import josie_agents.utils.log as log

# 加载环境变量
load_dotenv()


def test_josie_react_agent():
    """测试JosieReActAgent的功能"""

    # 创建LLM实例
    llm = JosieLLM()

    # 创建工具注册表
    tool_registry = ToolRegistry()

    # 注册一些基础工具用于测试
    log.info("🔧 注册测试工具...")

    # 注册计算器工具
    try:
        tool_registry.register_tool(Calculator())
        log.success("✅ 计算器工具注册成功")
    except ImportError:
        log.warn("⚠️ 计算器工具未找到，跳过注册")

    # 注册搜索工具（如果可用）
    try:

        search_tool = AdvancedSearchTool()

        tool_registry.register_function(
            name="advanced_search",
            description="高级搜索工具，整合Tavily和SerpAPI多个搜索源，提供更全面的搜索结果",
            func=search_tool.search
        )
        log.success("✅ 搜索工具注册成功")
    except ImportError:
        log.warn("⚠️ 搜索工具未找到，跳过注册")

    # 创建自定义ReActAgent
    agent = JosieReactAgent(
        name="我的推理行动助手",
        llm=llm,
        tool_registry=tool_registry,
        max_steps=5
    )

    log.delimiter("开始测试 JosieReActAgent")

    # 测试1：数学计算问题
    log.delimiter("📊 测试1：数学计算问题")
    math_question = "请帮我计算：(25 + 15) * 3 - 8 的结果是多少？"

    try:
        result1 = agent.run(math_question)
        log.info(f"🎯 测试1结果: {result1}")
    except Exception as e:
        log.error(f"❌ 测试1失败: {e}")

    # 测试2：需要搜索的问题
    log.delimiter("🔍 测试2：信息搜索问题")
    search_question = "Python编程语言是什么时候发布的？请告诉我具体的年份。"

    try:
        result2 = agent.run(search_question)
        log.info(f"🎯 测试2结果: {result2}")
    except Exception as e:
        log.error(f"❌ 测试2失败: {e}")

    # 测试3：复合问题（需要多步推理）
    log.delimiter("🧠 测试3：复合推理问题")
    complex_question = "如果一个班级有30个学生，其中60%是女生，那么男生有多少人？请先计算女生人数，再计算男生人数。"

    try:
        result3 = agent.run(complex_question)
        log.info(f"🎯 测试3结果: {result3}")
    except Exception as e:
        log.error(f"❌ 测试3失败: {e}")

    # 查看对话历史
    log.info(f"📝 对话历史记录: {len(agent.get_history())} 条消息")

    # 显示工具使用统计
    log.info(f"🛠️ 可用工具数量: {len(tool_registry._tools)}")
    log.info("已注册的工具:")
    for tool_name in tool_registry._tools.keys():
        log.info(f"  - {tool_name}")

    log.success("🎉 测试完成！")


def test_custom_prompt():
    """测试自定义提示词的ReActAgent"""

    log.delimiter("测试自定义提示词的 JosieReactAgent")

    # 创建LLM和工具注册表
    llm = JosieLLM()
    tool_registry = ToolRegistry()

    # 注册计算器工具
    try:
        tool_registry.register_tool(Calculator())
    except ImportError:
        pass

    # 自定义提示词（更简洁的版本）
    custom_prompt = """你是一个数学专家AI助手。

可用工具：{tools}

请按以下格式回应：
Thought: [你的思考]
Action: [tool_name[input] 或 Finish[答案]]

问题：{question}
历史：{history}

开始："""

    # 创建使用自定义提示词的Agent
    custom_agent = JosieReactAgent(
        name="数学专家助手",
        llm=llm,
        tool_registry=tool_registry,
        max_steps=3,
        custom_prompt=custom_prompt
    )

    # 测试数学问题
    math_question = "计算 15 × 8 + 32 ÷ 4 的结果"

    try:
        result = custom_agent.run(math_question)
        log.info(f"🎯 自定义提示词测试结果: {result}")
    except Exception as e:
        log.error(f"❌ 自定义提示词测试失败: {e}")


if __name__ == "__main__":
    # 运行基础测试
    test_josie_react_agent()

    # 运行自定义提示词测试
    test_custom_prompt()

    log.success("✨ 所有测试完成！")
