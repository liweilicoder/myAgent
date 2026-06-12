import os

from josie_agents.tools.registry import ToolRegistry
import josie_agents.utils.log as log
from typing import Dict, Any, List
from josie_agents.tools.base_tool import BaseTool, ToolParameter

import tavily
import serpapi

class AdvancedSearchTool(BaseTool):
    """
    自定义高级搜索工具类
    展示多源整合和智能选择的设计模式
    """

    def __init__(self):
        super().__init__(
            name="AdvancedSearch",
            description="智能搜索工具，支持多个搜索源，自动选择最佳结果"
        )
        self.search_sources = []
        self._setup_search_sources()

    def _setup_search_sources(self):
        """设置可用的搜索源"""
        # 检查Tavily可用性
        if os.getenv("TAVILY_API_KEY"):
            try:
                self.tavily_client = tavily.TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
                self.search_sources.append("tavily")
                log.success("✅ Tavily搜索源已启用")
            except ImportError:
                log.warn("⚠️ Tavily库未安装")

        # 检查SerpApi可用性
        if os.getenv("SERPAPI_API_KEY"):
            try:
                self.serpapi_client = serpapi.Client(api_key=os.getenv("SERPAPI_API_KEY"))
                self.search_sources.append("serpapi")
                log.success("✅ SerpApi搜索源已启用")
            except ImportError:
                log.warn("⚠️ SerpApi库未安装")

        if self.search_sources:
            log.info(f"🔧 可用搜索源: {', '.join(self.search_sources)}")
        else:
            log.error("⚠️ 没有可用的搜索源，请配置API密钥")


    def search(self, query: str) -> str:
        """执行智能搜索"""
        if not query.strip():
            return "❌ 错误：搜索查询不能为空"

        # 检查是否有可用的搜索源
        if not self.search_sources:
            return """❌ 没有可用的搜索源，请配置以下API密钥之一：

                    1. Tavily API: 设置环境变量 TAVILY_API_KEY
                        获取地址: https://tavily.com/

                    2. SerpAPI: 设置环境变量 SERPAPI_API_KEY
                    获取地址: https://serpapi.com/
                    
                    配置后重新运行程序。"""

        log.info(f"🔍 开始智能搜索: {query}")

        # 尝试多个搜索源，返回最佳结果
        for source in self.search_sources:
            try:
                if source == "tavily":
                    result = self._search_with_tavily(query)
                    if result and "未找到" not in result:
                        return f"📊 Tavily AI搜索结果：\n\n{result}"

                elif source == "serpapi":
                    result = self._search_with_serpapi(query)
                    if result and "未找到" not in result:
                        return f"🌐 SerpApi Google搜索结果：\n\n{result}"

            except Exception as e:
                print(f"⚠️ {source} 搜索失败: {e}")
                continue

        return "❌ 所有搜索源都失败了，请检查网络连接和API密钥配置"

    def _search_with_tavily(self, query: str) -> str:
        """使用Tavily搜索"""
        response = self.tavily_client.search(query=query, max_results=3)

        if response.get('answer'):
            result = f"💡 AI直接答案：{response['answer']}\n\n"
        else:
            result = ""

        result += "🔗 相关结果：\n"
        for i, item in enumerate(response.get('results', [])[:3], 1):
            result += f"[{i}] {item.get('title', '')}\n"
            result += f"    {item.get('content', '')[:150]}...\n\n"

        return result

    def _search_with_serpapi(self, query: str) -> str:
        """使用SerpApi搜索"""
        results = self.serpapi_client.search(q=query, engine="google", num=3)

        result = "🔗 Google搜索结果：\n"
        for i, res in enumerate(results.get("organic_results", [])[:3], 1):
            result += f"[{i}] {res.get('title', '')}\n"
            result += f"    {res.get('snippet', '')}\n\n"

        return result

    def run(self, parameters: Dict[str, Any]) -> str:
        return self.search(parameters['input'])

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="input",
                description="要搜索的信息",
                required=True
            )
        ]


def create_advanced_search_registry():
    """创建包含高级搜索工具的注册表"""
    registry = ToolRegistry()

    # 创建搜索工具实例
    search_tool = AdvancedSearchTool()

    # 注册搜索工具的方法作为函数
    registry.register_function(
        name="AdvancedSearch",
        description="高级搜索工具，整合Tavily和SerpAPI多个搜索源，提供更全面的搜索结果",
        func=search_tool.search
    )

    return registry

def test_advanced_search():
    """测试高级搜索工具"""

    # 创建包含计算器的注册表
    registry = create_advanced_search_registry()

    log.info("🧪 测试高级搜索工具\n")

    # 简单测试用例
    test_cases = [
        "美国的首都是哪里？",
        "今日金价多少钱？"
    ]

    for i, expression in enumerate(test_cases, 1):
        log.info(f"测试 {i}: {expression}")
        result = registry.execute_tool("AdvancedSearch", expression)
        log.info(f"结果: {result}\n")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    test_advanced_search()