"""
日志模块 - 提供带颜色的卡片式日志输出
"""
import inspect
import os
import re
import unicodedata

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
PURPLE = "\033[95m"
CYAN = "\033[96m"
GRAY = "\033[90m"

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
CARD_MIN_WIDTH = 50
INTERNAL_FUNCTIONS = {"_get_source", "_visible_width", "_pad", "_card", "_log", "_colored"}

def _get_source() -> str:
    """获取调用者的文件名和行号。"""
    frame = inspect.currentframe().f_back
    while frame:
        is_internal = frame.f_globals.get("__name__") == __name__ and (
            frame.f_code.co_name in INTERNAL_FUNCTIONS or not frame.f_code.co_name.startswith("_")
        )
        if not is_internal:
            break
        frame = frame.f_back
    if frame is None:
        return "unknown:0"
    filename = os.path.basename(frame.f_code.co_filename)
    lineno = frame.f_lineno
    return f"{filename}:{lineno}"

def _visible_width(text: str) -> int:
    text = ANSI_RE.sub("", str(text))
    width = 0
    for char in text:
        if unicodedata.combining(char) or unicodedata.category(char) in ("Mn", "Me", "Cf"):
            continue
        if char == "\t":
            width += 4
            continue
        if unicodedata.east_asian_width(char) in ("F", "W"):
            width += 2
        else:
            width += 1
    return width

def _pad(text: str, width: int) -> str:
    return text + " " * max(width - _visible_width(text), 0)

def _card(prefix: str, color: str, msg: str, msg_colored: bool = True) -> str:
    source = _get_source()
    title = f" {prefix} | {source} "
    lines = [line.replace("\t", "    ") for line in str(msg).splitlines()] or [""]
    content_width = max(CARD_MIN_WIDTH, _visible_width(title), *(_visible_width(line) for line in lines))

    top = f"{color}╭─{title}{'─' * (content_width - _visible_width(title))}─╮{RESET}"
    bottom = f"{color}╰{'─' * (content_width + 2)}╯{RESET}"
    body = []
    for line in lines:
        if msg_colored:
            line_str = f"{color}{_pad(line, content_width)}{RESET}"
        else:
            line_str = _pad(line, content_width)
        body.append(f"{color}│{RESET} {line_str} {color}│{RESET}")
    return "\n".join([top, *body, bottom])

def _log(prefix: str, color: str, msg: str, msg_colored: bool = True):
    print(_card(prefix, color, msg, msg_colored))

def _colored(prefix: str, color: str, msg: str, msg_colored: bool = True) -> str:
    """兼容旧的内部调用，统一走卡片输出。"""
    return _card(prefix, color, msg, msg_colored)

def info(msg: str, color_msg: bool = True):
    _log("Info", BLUE, msg, color_msg)

def warn(msg: str, color_msg: bool = True):
    _log("Warn", YELLOW, msg, color_msg)

def error(msg: str, color_msg: bool = True):
    _log("Error", RED, msg, color_msg)

def success(msg: str, color_msg: bool = True):
    _log("Success", GREEN, msg, color_msg)

def debug(msg: str, color_msg: bool = True):
    _log("Debug", GRAY, msg, color_msg)

def test(msg: str, color_msg: bool = True):
    _log("TEST", CYAN, msg, color_msg)

def stream(msg: str):
    """流式输出，不换行，立即显示"""
    print(f"{GRAY}{msg}{RESET}", end="", flush=True)

def delimiter(msg: str, color_msg: bool = True):
    _log("Delimiter", PURPLE, msg, color_msg)

def line_break():
    print()

def separator():
    print("=" * 50)
