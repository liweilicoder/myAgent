from typing import List, Dict, Any, Optional
from josie_agents.tools.registry import ToolRegistry
import josie_agents.utils.log as log

class ToolChain:
    """
    工具链 - 支持多个工具的顺序执行
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.steps: List[Dict[str, Any]] = []

    def add_step(self, tool_name: str, input_template: str, output_key: str = None):
        """
        添加工具执行步骤

        Args:
            tool_name: 工具名称
            input_template: 输入模板，支持变量替换
            output_key: 输出结果的键名，用于后续步骤引用
        """
        self.steps.append({
            "tool_name": tool_name,
            "input_template": input_template,
            "output_key": output_key or f"step_{len(self.steps)}_result"
        })

    def execute(self, registry: ToolRegistry, initial_input: str, context: Dict[str, Any] = None) -> str:
        """执行工具链"""
        context = context or {}
        context["input"] = initial_input

        log.info(f"🔗 开始执行工具链: {self.name}")

        for i, step in enumerate(self.steps, 1):
            tool_name = step["tool_name"]
            input_template = step["input_template"]
            output_key = step["output_key"]

            # 替换模板中的变量
            try:
                ## **叫关键字解包作用：把字典 “拆” 成 key=value 的形式传给函数
                tool_input = input_template.format(**context)
            except KeyError as e:
                return f"❌ 工具链执行失败:模板变量 {e} 未找到"

            log.info(f"  步骤 {i}: 使用 {tool_name} 处理 '{tool_input[:50]}...'")

            # 执行工具
            result = registry.execute_tool(tool_name, tool_input)
            context[output_key] = result

            log.success(f"  ✅ 步骤 {i} 完成，结果: {result} ")

        # 返回最后一步的结果
        final_result = context[self.steps[-1]["output_key"]]
        log.success(f"🎉 工具链 '{self.name}' 执行完成")
        return final_result


class ToolChainManager:
    """工具链管理器"""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.chains: Dict[str, ToolChain] = {}

    def register_chain(self, chain: ToolChain):
        """注册工具链"""
        self.chains[chain.name] = chain
        log.success(f"✅ 工具链 '{chain.name}' 已注册")

    def execute_chain(self, chain_name: str, input_data: str, context: Dict[str, Any] = None) -> str:
        """执行指定的工具链"""
        if chain_name not in self.chains:
            return f"❌ 工具链 '{chain_name}' 不存在"

        chain = self.chains[chain_name]
        return chain.execute(self.registry, input_data, context)

    def list_chains(self) -> List[str]:
        """列出所有工具链"""
        return list(self.chains.keys())

# 测试用例
def create_calculate_chain() -> ToolChain:
    """创建一个研究工具链:不停计算"""
    chain = ToolChain(
        name="calculate_and_calculate",
        description="不停计算"
    )

    # 步骤1:搜索信息
    chain.add_step(
        tool_name="Calculator",
        input_template="{input}",
        output_key="calculate1_result"
    )

    # 步骤2:基于搜索结果进行计算（如果需要）
    chain.add_step(
        tool_name="Calculator",
        input_template="3.14*({calculate1_result})",
        output_key="calculate2_result"
    )

    chain.add_step(
        tool_name="Calculator",
        input_template="({input}) + ({calculate2_result}) * ({calculate1_result})",
        output_key="calculate3_result"
    )

    return chain

if __name__ == "__main__":
    from josie_agents.tools.builtin.calculator import Calculator
    tool_registry = ToolRegistry()
    tool_registry.register_tool(Calculator())
    calculate_chain = create_calculate_chain()

    result = calculate_chain.execute(tool_registry, "889-34")
    log.info(f"链式计算最终结果: {result}")
