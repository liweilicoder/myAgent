from josie_agents.agents.josie_simple_agent import JosieSimpleAgent
from josie_agents.core.josie_llm import JosieLLM
from josie_agents.tools.builtin.protocol_tools import MCPTool
from josie_agents.utils import log


def test_simple_agent():
    log.delimiter("方式1：使用内置演示服务器")


    agent = JosieSimpleAgent(name="助手", llm=JosieLLM())

    # 无需任何配置，自动使用内置演示服务器
    # 内置服务器提供：add, subtract, multiply, divide, greet, get_system_info
    mcp_tool = MCPTool()  # 默认name="mcp"
    agent.add_tool(mcp_tool)

    # 智能体可以使用内置工具
    response = agent.run("计算 123 + 456")
    log.test(response)


if __name__ == "__main__":
    test_simple_agent()