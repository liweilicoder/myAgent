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

    # 连接到社区提供的文件系统服务器
    fs_tool = MCPTool(
        name="filesystem",  # 指定唯一名称
        description="访问本地文件系统",
        server_command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "."]
    )
    agent.add_tool(fs_tool)

    log.test("当前Agent拥有的工具：")

    for tool in agent.list_tools():
        log.test(f"- {tool}")

    # Agent现在可以自动使用这些工具！
    response = agent.run("请读取test_data/my_README.md文件，并总结其中的主要内容")
    log.test(response)




if __name__ == "__main__":
    test_simple_agent()

