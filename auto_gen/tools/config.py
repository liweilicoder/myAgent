import os
from typing import Optional

# 默认 biz 名称
DEFAULT_BIZ = "default"

# 全局 biz 配置，所有 Agent 操作文件时使用此 biz
_team_biz: Optional[str] = None

def set_team_biz(biz: str) -> None:
    """设置团队共享的 biz，调用后所有工具默认使用此 biz"""
    global _team_biz
    _team_biz = biz


def get_team_biz() -> Optional[str]:
    """获取团队共享的 biz"""
    return _team_biz


def get_output_dir(biz: Optional[str] = None) -> str:
    """
    获取输出目录路径，格式: auto_gen/output/${biz}
    biz 默认值为团队共享的 biz 或 DEFAULT_BIZ
    """
    if biz is None:
        biz = _team_biz if _team_biz else DEFAULT_BIZ
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "output",
        biz
    )
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


if __name__ == "__main__":
    print(get_output_dir(biz="exchange"))