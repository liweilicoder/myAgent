import asyncio

from josie_agents.protocols.mcp.client import MCPClient
from josie_agents.tools.builtin.protocol_tools import MCPTool
from josie_agents.utils import log


def mcp_memory_transport():
    log.delimiter(" 使用内置演示服务器（Memory传输） ")

    mcp_tool = MCPTool()

    # 列出可用工具
    result = mcp_tool.run({"action": "list_tools"})
    log.test(result)

    # 调用工具
    result = mcp_tool.run({
        "action": "call_tool",
        "tool_name": "add",
        "arguments": {"a": 10839583, "b": 2.32420}
    })
    log.test(result)

def mcp_stdio_transport():
    log.delimiter(" 使用社区服务器（文件系统）（Stdio传输） ")
    mcp_tool = MCPTool(server_command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "."])

    # 列出工具
    result = mcp_tool.run({"action": "list_tools"})
    log.test(result)

    # 调用工具
    result = mcp_tool.run({
        "action": "call_tool",
        "tool_name": "read_file",
        "arguments": {"path": "test_data/my_README.md"}
    })
    log.test(result)


# 注意：MCPTool 主要用于 Stdio 和 Memory 传输
# 对于 HTTP/SSE 等远程传输，建议使用底层的 MCPClient

def mcp_http_transport():
    log.delimiter(" 使用HTTP服务器（StreamHTTP传输） ")
    async def http_transport():
        # 连接到远程 HTTP MCP 服务器
        client = MCPClient("http://127.0.0.1:8000/mcp")

        async with client:
            # 获取服务器信息
            tools = await client.list_tools()
            log.test(f"远程服务器工具: {len(tools)} 个")

            # 调用远程工具
            result = await client.call_tool("str_upper", {
                "text": "Hello, World!"
            })
            log.test(f"远程处理结果: {result}")

    asyncio.run(http_transport())

if __name__ == "__main__":
    #mcp_memory_transport()

    #mcp_stdio_transport()

    # 需要先启动本地MCP服务器才能执行
    mcp_http_transport()