"""
NoteTool 基本操作示例

展示 NoteTool 的核心操作：
1. 创建笔记 (create)
2. 读取笔记 (read)
3. 更新笔记 (update)
4. 搜索笔记 (search)
5. 列出笔记 (list)
6. 笔记摘要 (summary)
7. 删除笔记 (delete)
"""

import re

from josie_agents.tools.builtin.note_tool import NoteTool
from josie_agents.utils import log


def extract_note_id(output: str) -> str:
    """从 NoteTool 的输出文本中提取 note_id"""
    match = re.search(r"ID:\s*(note_[0-9_]+)", output)
    if not match:
        raise ValueError(f"无法从输出解析 note_id:\n{output}")
    return match.group(1)


def main():
    log.delimiter("=" * 80)
    log.delimiter("NoteTool 基本操作示例")
    log.delimiter("=" * 80 + "\n")

    # 初始化 NoteTool
    notes = NoteTool(workspace="./project_notes")

    # 1. 创建笔记
    log.test("1. 创建笔记...")
    create_output_1 = notes.run({
        "action": "create",
        "title": "重构项目 - 第一阶段",
        "content": """## 完成情况
已完成数据模型层的重构,测试覆盖率达到85%。

## 下一步
重构业务逻辑层""",
        "note_type": "task_state",
        "tags": ["refactoring", "phase1"]
    })
    log.test(create_output_1 + "\n")
    note_id_1 = extract_note_id(create_output_1)

    # 创建第二个笔记
    create_output_2 = notes.run({
        "action": "create",
        "title": "依赖冲突问题",
        "content": """## 问题描述
发现某些第三方库版本不兼容,需要解决。

## 影响范围
业务逻辑层的3个模块

## 下一步
1. 使用虚拟环境隔离
2. 锁定版本
3. 使用 pipdeptree 分析依赖树""",
        "note_type": "blocker",
        "tags": ["dependency", "urgent"]
    })
    log.test(create_output_2 + "\n")
    note_id_2 = extract_note_id(create_output_2)

    # 2. 读取笔记
    log.test("2. 读取笔记...")
    note_detail = notes.run({
        "action": "read",
        "note_id": note_id_1
    })
    log.test(note_detail + "\n")

    # 3. 更新笔记
    log.test("3. 更新笔记...")
    update_result = notes.run({
        "action": "update",
        "note_id": note_id_1,
        "content": """## 完成情况
已完成数据模型层的重构,测试覆盖率达到85%。

## 问题
遇到依赖版本冲突,已记录到单独笔记。

## 下一步
先解决依赖冲突,再继续重构业务逻辑层"""
    })
    log.test(update_result + "\n")

    # 4. 搜索笔记
    log.test("4. 搜索笔记...")
    search_results = notes.run({
        "action": "search",
        "query": "依赖",
        "limit": 5
    })
    log.test(search_results + "\n")

    # 5. 列出笔记
    log.test("5. 列出所有 blocker 类型的笔记...")
    blockers = notes.run({
        "action": "list",
        "note_type": "blocker",
        "limit": 10
    })
    log.test(blockers + "\n")

    # 6. 笔记摘要
    log.test("6. 生成笔记摘要...")
    summary_output = notes.run({
        "action": "summary"
    })
    log.test(summary_output + "\n")

    # 7. 删除笔记 (演示，实际使用时谨慎)
    log.test("7. 删除笔记 (演示)...")
    delete_result = notes.run({
        "action": "delete",
        "note_id": note_id_2
    })
    log.test(delete_result + "\n")
    log.test(f"(已跳过实际删除操作, 笔记ID: {note_id_2})\n")

    log.success("=" * 80)
    log.success("NoteTool 操作演示完成!")
    log.success("=" * 80)


if __name__ == "__main__":
    main()
