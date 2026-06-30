"""
TerminalTool 使用示例

展示 TerminalTool 的典型使用模式：
1. 探索式导航
2. 数据文件分析
3. 日志文件分析
4. 代码库分析
"""

from pathlib import Path

from josie_agents.tools.builtin.terminal_tool import TerminalTool
from josie_agents.utils import log

# 获取脚本所在目录
SCRIPT_DIR = Path(__file__).parent.absolute()


def assert_allowed(result: str, expected: str = ""):
    """安全命令应该成功，并可选检查关键输出。"""
    assert not result.startswith("❌"), result
    assert "不允许访问工作目录外" not in result, result
    if expected:
        assert expected in result, result


def assert_rejected(result: str):
    """危险命令必须被拒绝，而不是靠系统命令失败碰运气。"""
    assert result.startswith("❌"), result


def test_exploratory_navigation():
    """演示探索式导航"""
    log.test("=" * 80)
    log.test("场景1: 探索式导航")
    log.test("=" * 80 + "\n")

    terminal = TerminalTool(workspace=str(SCRIPT_DIR))

    # 第一步:查看当前目录
    log.test("1. 查看当前目录:")
    result = terminal.run({"command": "ls -la"})
    log.test(result)
    assert_allowed(result, "codebase_maintainer.py")

    # 第二步:查看Python文件
    log.test("\n2. 查看Python文件:")
    result = terminal.run({"command": "ls -la *.py"})
    log.test(result)
    assert_allowed(result, "test_terminal_tool.py")

    # 第三步:查找特定文件
    log.test("\n3. 查找特定模式的文件:")
    result = terminal.run({"command": "find . -name '*codebase_maintainer.py'"})
    log.test(result)
    assert_allowed(result, "codebase_maintainer.py")

    # 第四步:查看文件内容
    log.test("\n4. 查看文件内容:")
    result = terminal.run({"command": "head -n 20 codebase_maintainer.py"})
    log.test(result)
    assert_allowed(result, "TerminalTool")


def test_data_file_analysis():
    """演示数据文件分析"""
    log.test("=" * 80)
    log.test("场景2: 数据文件分析")
    log.test("=" * 80 + "\n")

    terminal = TerminalTool(workspace=str(SCRIPT_DIR / "data"))

    # 查看 CSV 文件的前几行
    log.test("1. 查看 CSV 文件前5行:")
    result = terminal.run({"command": "head -n 5 sales_2024.csv"})
    log.test(result)
    assert_allowed(result, "Laptop Pro")

    # 统计总行数
    log.test("2. 统计文件行数:")
    result = terminal.run({"command": "wc -l *.csv"})
    log.test(result)
    assert_allowed(result, "sales_2024.csv")

    # 提取和统计产品类别
    log.test("3. 提取产品类别列:")
    result = terminal.run({"command": "cut -d, -f3 sales_2024.csv"})
    log.test(result)
    assert_allowed(result, "Electronics")


def test_log_analysis():
    """演示日志文件分析"""
    log.test("=" * 80)
    log.test("场景3: 日志文件分析")
    log.test("=" * 80 + "\n")

    terminal = TerminalTool(workspace=str(SCRIPT_DIR / "logs"))

    # 查看最新的错误日志
    log.test("1. 查看最新的错误日志:")
    result = terminal.run({"command": "grep ERROR app.log"})
    log.test(result)
    assert_allowed(result, "DB_TIMEOUT")

    # 统计错误类型分布
    log.test("2. 提取日志模块列:")
    result = terminal.run({"command": "cut -d ' ' -f4 app.log"})
    log.test(result)
    assert_allowed(result, "database")

    # 查找特定时间段的日志
    log.test("3. 查找特定时间段的日志:")
    result = terminal.run({"command": "grep '2024-01-19 15:' app.log"})
    log.test(result)
    assert_allowed(result, "15:45:30")


def test_codebase_analysis():
    """演示代码库分析"""
    log.test("=" * 80)
    log.test("场景4: 代码库分析")
    log.test("=" * 80 + "\n")

    terminal = TerminalTool(workspace=str(SCRIPT_DIR / "codebase"))

    # 统计代码行数
    log.test("1. 查找 Python 文件:")
    result = terminal.run({"command": "find . -name '*.py'"})
    log.test(result)
    assert_allowed(result, "data_processor.py")

    # 查找所有 TODO 注释
    log.test("2. 查找所有 TODO 注释:")
    result = terminal.run({"command": "grep -rn TODO --include='*.py' ."})
    log.test(result)
    assert_allowed(result, "TODO")

    # 查找特定函数的定义
    log.test("3. 查找特定函数的定义:")
    result = terminal.run({"command": "grep -rn 'def process_data' --include='*.py' ."})
    log.test(result)
    assert_allowed(result, "process_data")


def test_security_features():
    """演示安全特性"""
    log.test("=" * 80)
    log.test("安全特性演示")
    log.test("=" * 80 + "\n")

    terminal = TerminalTool(workspace=str(SCRIPT_DIR / "project"))

    # 尝试执行不允许的命令
    log.test("1. 尝试执行危险命令 (rm):")
    result = terminal.run({"command": "rm -rf /"})
    log.test(result)
    assert_rejected(result)

    # 尝试访问工作目录外的文件
    log.test("2. 尝试访问工作目录外的文件:")
    result = terminal.run({"command": "cat /etc/passwd"})
    log.test(result)
    assert_rejected(result)

    log.test("3. 尝试用 head 访问工作目录外的文件:")
    result = terminal.run({"command": "head -n 1 /etc/passwd"})
    log.test(result)
    assert_rejected(result)

    log.test("4. 尝试通过相对路径读取工作目录外文件:")
    result = terminal.run({"command": "cat ../test_terminal_tool.py"})
    log.test(result)
    assert_rejected(result)

    log.test("5. 尝试通过管道绕过路径限制:")
    result = terminal.run({"command": "echo ok | cat /etc/passwd"})
    log.test(result)
    assert_rejected(result)

    log.test("6. 尝试通过 bash 绕过路径限制:")
    result = terminal.run({"command": "bash -lc 'cat /etc/passwd'"})
    log.test(result)
    assert_rejected(result)

    log.test("7. 尝试通过 find -exec 绕过路径限制:")
    result = terminal.run({"command": "find . -exec cat /etc/passwd \\;"})
    log.test(result)
    assert_rejected(result)

    log.test("8. 尝试通过 grep -e 读取工作目录外文件:")
    result = terminal.run({"command": "grep -e root /etc/passwd"})
    log.test(result)
    assert_rejected(result)

    log.test("9. 尝试通过 grep -f 读取工作目录外 pattern 文件:")
    result = terminal.run({"command": "grep -f /etc/passwd README.md"})
    log.test(result)
    assert_rejected(result)

    log.test("10. 尝试通过 grep -f 读取工作目录外目标文件:")
    result = terminal.run({"command": "grep -f README.md /etc/passwd"})
    log.test(result)
    assert_rejected(result)

    # 尝试逃逸工作目录
    log.test("11. 尝试通过 .. 逃逸工作目录:")
    current_dir = terminal.get_current_dir()
    result = terminal.run({"command": "cd ../../../etc"})
    log.test(result)
    assert_rejected(result)
    assert terminal.get_current_dir() == current_dir

    log.test("12. 确认工作目录内文件仍可访问:")
    result = terminal.run({"command": "cat README.md"})
    log.test(result)
    assert_allowed(result, "项目演示目录")


def main():
    log.delimiter("=" * 80)
    log.delimiter("TerminalTool 使用示例")
    log.delimiter("=" * 80)

    # 演示各种使用场景
    test_exploratory_navigation()
    test_data_file_analysis()
    test_log_analysis()
    test_codebase_analysis()
    test_security_features()

    log.delimiter("=" * 80)
    log.delimiter("演示完成!")
    log.delimiter("=" * 80)


if __name__ == "__main__":
    main()
