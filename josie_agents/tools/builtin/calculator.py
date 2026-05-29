import ast
import operator
import math

from josie_agents.tools.registry import ToolRegistry
from josie_agents.tools.base_tool import BaseTool, ToolParameter
import josie_agents.utils.log as log
from typing import Dict, Any, List

class Calculator(BaseTool):
    """
    计算器工具类
    """

    def __init__(self):
        super().__init__(
            name="Calculator",
            description="简单的数学计算工具，支持基本运算(+,-,*,/)和sqrt函数"
        )

    def run(self, parameters: Dict[str, Any]) -> str:
        return calculate(parameters['input'])

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="input",
                description="要计算的数学表达式",
                required=True
            )
        ]


def calculate(expression: str) -> str:
    """简单的数学计算函数"""
    if not expression.strip():
        return "计算表达式不能为空"

    # 支持的基本运算
    operators = {
        ast.Add: operator.add,  # +
        ast.Sub: operator.sub,  # -
        ast.Mult: operator.mul,  # *
        ast.Div: operator.truediv,  # /
    }

    # 支持的基本函数
    functions = {
        'sqrt': math.sqrt,
        'pi': math.pi,
    }

    try:
        node = ast.parse(expression, mode='eval')
        result = _eval_node(node.body, operators, functions)
        return str(result)
    except:
        return "计算失败，请检查表达式格式"

def _eval_node(node, operators, functions):
    """简化的表达式求值"""
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left, operators, functions)
        right = _eval_node(node.right, operators, functions)
        op = operators.get(type(node.op))
        return op(left, right)
    elif isinstance(node, ast.Call):
        func_name = node.func.id
        if func_name in functions:
            args = [_eval_node(arg, operators, functions) for arg in node.args]
            return functions[func_name](*args)
    elif isinstance(node, ast.Name):
        if node.id in functions:
            return functions[node.id]


def test_calculator_tool():
    """测试自定义计算器工具"""

    # 创建包含计算器的注册表
    registry = ToolRegistry()
    calculator = Calculator()
    registry.register_tool(calculator)

    log.info("🧪 测试自定义计算器工具\n")

    # 简单测试用例
    test_cases = [
        "2 + 3 - 5",           # 基本加法
        "10 - 4355",           # 基本减法
        "5 * 66666666",        # 基本乘法
        "15 / 36",             # 基本除法
        "sqrt(11)",            # 平方根
    ]

    for i, expression in enumerate(test_cases, 1):
        log.info(f"测试 {i}: {expression}")
        result = registry.execute_tool("Calculator", expression)
        log.info(f"结果: {result}\n")


if __name__ == "__main__":
    test_calculator_tool()
