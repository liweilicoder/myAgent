import os
from pathlib import Path
from typing import Annotated
from dotenv import load_dotenv

load_dotenv()

# 全局目录变量
WORK_DIR = ""


def init_output_dirs(project: str, biz: str) -> dict:
    """初始化输出目录，所有文件平铺在同一目录下"""
    global WORK_DIR

    output_dir = Path(project) / biz
    output_dir.mkdir(parents=True, exist_ok=True)

    WORK_DIR = str(output_dir)

    return {"output": str(output_dir)}


def save_file(
    filename: Annotated[str, "文件名，如 main.py 或 prd.md"],
    content: Annotated[str, "文件内容"]
) -> str:
    """保存文件到输出目录"""
    filename = Path(filename).name
    file_path = os.path.join(WORK_DIR, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"✅ 文件已保存至：{file_path}"


def read_file(
    filename: Annotated[str, "待读取文件名"]
) -> str:
    """读取文件内容"""
    filename = Path(filename).name
    file_path = os.path.join(WORK_DIR, filename)
    if not os.path.exists(file_path):
        return f"❌ 文件不存在：{file_path}"
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()