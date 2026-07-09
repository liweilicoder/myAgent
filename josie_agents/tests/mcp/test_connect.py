import asyncio

from josie_agents.protocols.mcp.client import MCPClient
from josie_agents.tools.builtin.protocol_tools import MCPTool
from josie_agents.utils import log

from dotenv import load_dotenv
load_dotenv()


def builtin_mcp_connect():
    log.delimiter("测试 builtin_mcp_connect")

    mcp_tool = MCPTool()

    result = mcp_tool.run({
        "action": "call_tool",
        "tool_name": "add",
        "arguments": {"a": 10, "b": 20}
    })
    log.test(f"MCP计算结果: {result}")  # 输出: 30.0


def mcp_discover_tools():
    log.delimiter("测试 discover_tools")

    async def discover_tools():
        client = MCPClient(["npx", "-y", "@modelcontextprotocol/server-filesystem", "."])

        async with client:
            # 获取所有可用工具
            tools = await client.list_tools()

            log.test(f"服务器提供了 {len(tools)} 个工具：")
            for tool in tools:
                log.test(f" 工具名称: {tool['name']} \n"
                         f" 描述: {tool.get('description', '无描述')}")

                # 打印参数信息
                if 'inputSchema' in tool:
                    schema = tool['inputSchema']
                    if 'properties' in schema:
                        log.test("参数:")
                        for param_name, param_info in schema['properties'].items():
                            param_type = param_info.get('type', 'any')
                            param_desc = param_info.get('description', '')
                            log.test(f"  - {param_name} ({param_type}): {param_desc}")

    asyncio.run(discover_tools())


def mcp_use_tools():
    log.delimiter("测试 use_tools")

    async def use_tools():
        client = MCPClient(["npx", "-y", "@modelcontextprotocol/server-filesystem", "."])

        async with client:
            # 读取文件
            result = await client.call_tool("read_file", {"path": "test_data/my_README.md"})
            log.test(f"文件内容：\n{result}")

            # 列出目录
            result = await client.call_tool("list_directory", {"path": "test_data"})
            log.test(f"当前目录文件：\n{result}")

            # 写入文件
            result = await client.call_tool("write_file", {
                "path": "test_data/output.txt",
                "content": "Hello Josie! From Jesse"
            })
            log.test(f"写入结果：{result}")

    asyncio.run(use_tools())

def mcp_safe_tool_call():
    log.delimiter("测试 tool_call")
    async def safe_tool_call():
        client = MCPClient(["npx", "-y", "@modelcontextprotocol/server-filesystem", "."])

        async with client:
            try:
                # 尝试读取可能不存在的文件
                result = await client.call_tool("read_file", {"path": "test_data/nonexistent.txt"})
                log.test(result)
            except Exception as e:
                log.warn(f"工具调用失败: {e}")
                # 可以选择重试、使用默认值或向用户报告错误

    asyncio.run(safe_tool_call())

def github_mcp():
    log.delimiter("测试 github_mcp")

    # 创建 GitHub MCP 工具
    github_tool = MCPTool(
        server_command=["npx", "-y", "@modelcontextprotocol/server-github"]
    )

    # 1. 列出可用工具
    result = github_tool.run({"action": "list_tools"})
    log.test(f"📋 可用工具：{result}")

    # 2. 搜索仓库
    result = github_tool.run({
        "action": "call_tool",
        "tool_name": "search_repositories",
        "arguments": {
            "query": "AI agents language:python",
            "page": 1,
            "perPage": 3
        }
    })
    log.test(f"🔍 搜索仓库：{result}")

if __name__ == "__main__":
    #builtin_mcp_connect()

    #mcp_discover_tools()

    #mcp_use_tools()

    #mcp_safe_tool_call()

    github_mcp()






