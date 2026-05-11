from typing import Dict, Any
import hello_agent.logger.logger as log
import hello_agent.tools.search as search

class ToolExecutor:
    """
    一个工具执行器，负责管理和执行工具。
    """

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def registerTool(self, name: str, description: str, func: callable):
        """
        向工具箱中注册一个新工具。
        """
        if name in self.tools:
            log.warn(f"警告：工具 '{name}' 已存在，将被覆盖。")

        self.tools[name] = {"description": description, "func": func}
        log.success(f"工具 '{name}' 已注册。")

    def getTool(self, name: str) -> callable:
        """
        根据名称获取一个工具的执行函数。
        """
        return self.tools.get(name, {}).get("func")

    def getAvailableTools(self) -> str:
        """
        获取所有可用工具的格式化描述字符串。
        """
        return "\n".join([
            f"- {name}: {info['description']}"
            for name, info in self.tools.items()
        ])


# --- 工具初始化与使用示例 ---
if __name__ == '__main__':
    toolExecutor = ToolExecutor()

    search_description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    toolExecutor.registerTool("Search", search_description, search.search)

    log.debug("--- 可用的工具 ---")
    log.debug(toolExecutor.getAvailableTools())

    log.debug("--- 执行 Action: Search['华为最新的手机型号是什么？'] ---")
    tool_name = "Search"
    tool_input = "华为最新的手机型号是什么？"

    tool_function = toolExecutor.getTool(tool_name)
    if tool_function:
        observation = tool_function(tool_input)
        log.debug("--- 观察 (Observation) ---")
        log.debug(observation)
    else:
        log.error(f"错误：未找到名为 '{tool_name}' 的工具。")
