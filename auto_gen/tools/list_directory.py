import os
from typing import List, Optional

from auto_gen.tools.config import get_output_dir


def list_directory(path: str = ".", biz: Optional[str] = None) -> List[str]:
    """列出目录中的文件"""
    output_dir = get_output_dir(biz)
    if path == ".":
        full_path = output_dir
    else:
        full_path = os.path.join(output_dir, path)
    if os.path.exists(full_path):
        return os.listdir(full_path)
    return []