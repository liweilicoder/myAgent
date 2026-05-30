import asyncio
import concurrent.futures
from typing import Dict, Any, List, Callable
from josie_agents.tools.registry import ToolRegistry
import josie_agents.utils.log as log

class AsyncToolExecutor:
    """异步工具执行器"""

    def __init__(self, registry: ToolRegistry, max_workers: int = 4):
        self.registry = registry
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    async def execute_tool_async(self, tool_name: str, input_data: str) -> str:
        """异步执行单个工具"""
        loop = asyncio.get_event_loop()

        def _execute():
            return self.registry.execute_tool(tool_name, input_data)

        result = await loop.run_in_executor(self.executor, _execute)
        return result

    async def execute_tools_parallel(self, tasks: List[Dict[str, str]]) -> List[str]:
        """并行执行多个工具"""
        log.info(f"🚀 开始并行执行 {len(tasks)} 个工具任务")

        # 创建异步任务
        async_tasks = []
        for task in tasks:
            tool_name = task["tool_name"]
            input_data = task["input_data"]
            async_task = self.execute_tool_async(tool_name, input_data)
            async_tasks.append(async_task)

        # 等待所有任务完成
        results = await asyncio.gather(*async_tasks)

        log.success(f"✅ 所有工具任务执行完成")
        return results

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)

# 使用示例
async def test_parallel_execution():
    """测试并行工具执行"""

    registry = ToolRegistry()

    from josie_agents.tools.builtin.calculator import Calculator
    from josie_agents.tools.builtin.advanced_search import AdvancedSearchTool
    registry.register_tool(Calculator())
    registry.register_tool(AdvancedSearchTool())
    # 假设已经注册了搜索和计算工具

    executor = AsyncToolExecutor(registry)

    # 定义并行任务
    tasks = [
        {"tool_name": "AdvancedSearch", "input_data": "Python编程"},
        {"tool_name": "AdvancedSearch", "input_data": "机器学习"},
        {"tool_name": "Calculator", "input_data": "2 + 2 - 4545-555*345"},
        {"tool_name": "Calculator", "input_data": "sqrt(16342523524234)"},
    ]

    # 并行执行
    results = await executor.execute_tools_parallel(tasks)

    for i, result in enumerate(results):
        log.info(f"任务 {i+1} 结果: {result[:1000]}...")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    asyncio.run(test_parallel_execution())