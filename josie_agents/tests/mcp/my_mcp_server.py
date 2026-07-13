from fastmcp import FastMCP

# 初始化MCP服务
mcp = FastMCP("RemoteDemoServer", version="1.0.0")

# 示例工具1：数学计算
@mcp.tool()
def calc_add(a: float, b: float) -> float:
    """两数相加"""
    return a + b

# 示例工具2：字符串处理
@mcp.tool()
def str_upper(text: str) -> str:
    """字符串转大写"""
    return text.upper()

# 示例资源
@mcp.resource("config://info")
def get_server_info() -> str:
    return "远程HTTP MCP演示服务 | Streamable HTTP Transport"

if __name__ == "__main__":
    # 启动远程HTTP服务，0.0.0.0 允许内网/外网访问
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000
    )