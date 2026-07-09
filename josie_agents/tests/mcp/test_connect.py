from josie_agents.tools.builtin.protocol_tools import MCPTool
from josie_agents.utils import log


def main():
    mcp_tool = MCPTool()

    result = mcp_tool.run({
        "action": "call_tool",
        "tool_name": "add",
        "arguments": {"a": 10, "b": 20}
    })
    log.test(f"MCP计算结果: {result}")  # 输出: 30.0

if __name__ == "__main__":
    main()




