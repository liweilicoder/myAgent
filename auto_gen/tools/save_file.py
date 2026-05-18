import os
from typing import Optional

from auto_gen.tools.config import get_output_dir


def save_file(filename: str, content: str, biz: Optional[str] = None) -> str:
    """保存内容到本地文件"""
    output_dir = get_output_dir(biz)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath