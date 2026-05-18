import os
from typing import Optional

from auto_gen.tools.config import get_output_dir


def read_file(filepath: str, biz: Optional[str] = None) -> str:
    """读取文件内容"""
    output_dir = get_output_dir(biz)
    full_path = os.path.join(output_dir, filepath)

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"文件不存在: {full_path}")
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()