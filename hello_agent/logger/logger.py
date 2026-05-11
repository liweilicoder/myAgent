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

def _colored(prefix: str, color: str, msg: str, msg_colored: bool = False) -> str:
    source = _get_source()
    prefix_str = f"{color}[{prefix}][{source}]{RESET}"
    if msg_colored:
        msg_str = f"{color}{msg}{RESET}"
    else:
        msg_str = msg
    return f"{prefix_str} {msg_str}"

def info(msg: str, color_msg: bool = False):
    print(_colored("Info", BLUE, msg, color_msg))

def warn(msg: str, color_msg: bool = False):
    print(_colored("Warn", YELLOW, msg, color_msg))

def error(msg: str, color_msg: bool = False):
    print(_colored("Error", RED, msg, color_msg))

def success(msg: str, color_msg: bool = False):
    print(_colored("Success", GREEN, msg, color_msg))

def debug(msg: str, color_msg: bool = False):
    print(_colored("Debug", PURPLE, msg, color_msg))

def stream(msg: str):
    """流式输出，不换行，立即显示"""
    print(f"{YELLOW}{msg}{RESET}", end="", flush=True)

def separator():
    print("=" * 50)
