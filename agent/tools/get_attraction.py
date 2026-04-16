import os
from tavily import TavilyClient
from dotenv import load_dotenv
import agent.logger as log

load_dotenv('/Users/jesse/PythonProjects/myAgent/.env', override=True)

def get_attraction(city: str, weather: str) -> str:
    """
    根据城市和天气，使用Tavily Search API搜索并返回优化后的景点推荐。
    """
    log.info(f"搜索景点: {city}, 天气: {weather}")

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        log.warn("未配置 TAVILY_API_KEY")
        return "错误：未配置TAVILY_API_KEY。"

    tavily = TavilyClient(api_key=api_key)
    query = f"'{city}' 在'{weather}'天气下最值得去的旅游景点推荐及理由"

    try:
        response = tavily.search(query=query, search_depth="basic", include_answer=True)

        if response.get("answer"):
            log.info("获取到 Tavily 答案")
            return response["answer"]

        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}: {result['content']}")

        if not formatted_results:
            log.warn("未找到相关景点推荐")
            return "抱歉，没有找到相关的旅游景点推荐。"

        log.info("返回格式化搜索结果")
        return "根据搜索，为您找到以下信息：\n" + "\n".join(formatted_results)

    except Exception as e:
        log.warn(f"Tavily 搜索出错 - {e}")
        return f"错误：执行Tavily搜索时出现问题 - {e}"
