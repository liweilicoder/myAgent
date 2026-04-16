"""
日志模块 - 提供带颜色的日志输出
"""
import inspect
import os

RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
PURPLE = "\033[95m"
CYAN = "\033[96m"

def _get_source() -> str:
    """获取调用者的文件名和行号（回溯三级：_get_source -> _colored -> info -> 调用者）"""
    frame = inspect.currentframe().f_back.f_back.f_back
    filename = os.path.basename(frame.f_code.co_filename)
    lineno = frame.f_lineno
    return f"{filename}:{lineno}"

def _colored(prefix: str, color: str, msg: str) -> str:
    source = _get_source()
    return f"{color}[{prefix}][{source}]{RESET} {msg}"

def info(msg: str):
    print(_colored("Info", CYAN, msg))

def warn(msg: str):
    print(_colored("Warn", YELLOW, msg))

def error(msg: str):
    print(_colored("Error", RED, msg))

def success(msg: str):
    print(_colored("Success", GREEN, msg))

def debug(msg: str):
    print(_colored("Debug", PURPLE, msg))

def separator():
    print("=" * 50)
