from josie_agents.tools.builtin.protocol_tools import MCPTool
from josie_agents.utils import log


def mcp_memory():
    log.delimiter(" 使用内置演示服务器（Memory传输） ")

    mcp_tool = MCPTool()

    # 列出可用工具
    result = mcp_tool.run({"action": "list_tools"})
    log.test(result)

    # 调用工具
    result = mcp_tool.run({
        "action": "call_tool",
        "tool_name": "add",
        "arguments": {"a": 10, "b": 20}
    })
    log.test(result)



if __name__ == "__main__":
    mcp_memory()