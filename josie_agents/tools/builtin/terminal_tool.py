"""TerminalTool - 命令行工具

为Agent提供安全的命令行执行能力，支持：
- 文件系统操作（ls, cat, head, tail, find, grep）
- 文本处理（wc, sort, uniq）
- 目录导航（pwd, cd）
- 安全限制（白名单命令、路径限制、超时控制）

使用场景：
- JIT（即时）文件检索与分析
- 代码仓库探索
- 日志文件分析
- 数据文件预览

安全特性：
- 命令白名单（只允许安全的只读命令）
- 工作目录限制（沙箱）
- 超时控制
- 输出大小限制
- 禁止危险操作（rm, mv, chmod等）
"""

from typing import Dict, Any, List, Tuple
import subprocess
import os
from pathlib import Path
import shlex

from josie_agents.tools.base_tool import BaseTool, ToolParameter
from josie_agents.utils import log


class TerminalTool(BaseTool):
    """命令行工具

    提供安全的命令行执行能力，支持常用的文件系统和文本处理命令。

    安全限制：
    - 只允许白名单中的命令
    - 限制在指定工作目录内
    - 超时控制（默认30秒）
    - 输出大小限制（默认10MB）

    用法示例：
    ```python
    terminal = TerminalTool(workspace="./project")

    # 列出文件
    result = terminal.run({"command": "ls -la"})

    # 查看文件内容
    result = terminal.run({"command": "cat README.md"})

    # 搜索文件
    result = terminal.run({"command": "grep -r 'TODO' src/"})

    # 查看文件前10行
    result = terminal.run({"command": "head -n 10 data.csv"})
    ```
    """

    # 允许的命令白名单
    ALLOWED_COMMANDS = {
        # 文件列表与信息
        'ls', 'dir', 'tree',
        # 文件内容查看
        'cat', 'head', 'tail',
        # 文件搜索
        'find', 'grep', 'egrep', 'fgrep',
        # 文本处理
        'wc', 'sort', 'uniq', 'cut',
        # 目录操作
        'pwd', 'cd',
        # 文件信息
        'file', 'stat', 'du',
        # 其他
        'echo',
    }

    SHELL_META_TOKENS = {'|', ';', '&', '&&', '||', '<', '>', '>>', '2>', '2>>'}
    SHELL_META_CHARS = {'|', ';', '&', '<', '>', '`'}
    FIND_FORBIDDEN_ACTIONS = {
        '-delete', '-exec', '-execdir', '-ok', '-okdir',
        '-fls', '-fprint', '-fprint0', '-fprintf',
    }
    PATH_OPTION_VALUE_FLAGS = {
        '-n', '--lines',
        '-c', '--bytes',
        '-d', '--delimiter',
        '-f', '--fields',
    }
    GREP_OPTION_VALUE_FLAGS = {
        '-m', '--max-count',
        '-A', '--after-context',
        '-B', '--before-context',
        '-C', '--context',
        '-e', '--regexp',
        '--include', '--exclude', '--exclude-dir',
    }
    GREP_FILE_OPTION_VALUE_FLAGS = {'-f', '--file'}

    def __init__(
        self,
        workspace: str = ".",
        timeout: int = 30,
        max_output_size: int = 10 * 1024 * 1024,  # 10MB
        allow_cd: bool = True
    ):
        super().__init__(
            name="terminal",
            description="命令行工具 - 执行安全的文件系统、文本处理和代码执行命令（ls, cat, grep, head, tail等）"
        )

        self.workspace = Path(workspace).resolve()
        self.timeout = timeout
        self.max_output_size = max_output_size
        self.allow_cd = allow_cd

        # 当前工作目录（相对于workspace）
        self.current_dir = self.workspace

        # 确保工作目录存在
        self.workspace.mkdir(parents=True, exist_ok=True)
        log.success("⛰️ TerminalTool 初始化完成")

    def run(self, parameters: Dict[str, Any]) -> str:
        """执行工具"""
        if not self.validate_parameters(parameters):
            return "❌ 参数验证失败"

        command = parameters.get("command", "").strip()

        if not command:
            return "❌ 命令不能为空"

        # 解析命令
        try:
            parts = shlex.split(command)
        except ValueError as e:
            return f"❌ 命令解析失败: {e}"

        if not parts:
            return "❌ 命令不能为空"

        base_command = parts[0]

        log.info(f"⛰️[TerminalTool] command: {base_command}, parameters: {parts[1:]}")

        # 检查命令是否在白名单中
        if base_command not in self.ALLOWED_COMMANDS:
            log.error(f"❌ 不允许的命令: {base_command}\n允许的命令: {', '.join(sorted(self.ALLOWED_COMMANDS))}")
            return f"❌ 不允许的命令: {base_command}\n允许的命令: {', '.join(sorted(self.ALLOWED_COMMANDS))}"

        # 特殊处理 cd 命令
        if base_command == 'cd':
            return self._handle_cd(parts)

        safe_parts, validation_error = self._validate_and_expand_command(parts)
        if validation_error:
            log.error(validation_error)
            return validation_error

        # 执行命令
        return self._execute_command(safe_parts)

    def get_parameters(self) -> List[ToolParameter]:
        """获取工具参数定义"""
        return [
            ToolParameter(
                name="command",
                type="string",
                description=(
                    f"要执行的命令（白名单: {', '.join(sorted(self.ALLOWED_COMMANDS)[:10])}...）\n"
                    "示例: 'ls -la', 'cat file.txt', 'grep pattern *.py', 'head -n 20 data.csv'"
                ),
                required=True
            ),
        ]

    def _handle_cd(self, parts: List[str]) -> str:
        """处理 cd 命令"""
        if not self.allow_cd:
            return "❌ cd 命令已禁用"

        if len(parts) < 2:
            # cd 无参数，返回当前目录
            log.info("⛰️ [TerminalTool] [cd] return current directory")
            return f"当前目录: {self.current_dir}"

        target_dir = parts[1]
        new_dir, path_error = self._resolve_workspace_path(target_dir)
        if path_error:
            log.error(path_error)
            return path_error

        log.info(f"⛰️ [TerminalTool] [cd] target dir={new_dir}")

        # 检查目录是否存在
        if not new_dir.exists():
            log.error(f"❌ 目录不存在: {new_dir}")
            return f"❌ 目录不存在: {new_dir}"

        if not new_dir.is_dir():
            log.error(f"❌ 不是目录: {new_dir}")
            return f"❌ 不是目录: {new_dir}"

        # 更新当前目录
        self.current_dir = new_dir
        log.success(f"⛰️ [TerminalTool] [cd] 切换到目录: {self.current_dir}")
        return f"✅ 切换到目录: {self.current_dir}"

    def _validate_and_expand_command(self, parts: List[str]) -> Tuple[List[str], str]:
        """校验命令参数中的路径，并在工作目录内展开基础 glob。"""
        command = parts[0]

        if command in {'pwd', 'echo'}:
            return parts, ""

        if command == 'find':
            return self._validate_find(parts)

        option_error = self._validate_command_options(command, parts)
        if option_error:
            return [], option_error

        path_indexes = self._path_argument_indexes(command, parts)
        if command == 'uniq' and len(path_indexes) > 1:
            return [], "❌ uniq 不允许指定输出文件"

        return self._replace_path_args(parts, path_indexes)

    def _validate_find(self, parts: List[str]) -> Tuple[List[str], str]:
        """find 只允许查找，不允许执行或写文件。"""
        for token in parts[1:]:
            if token in self.FIND_FORBIDDEN_ACTIONS:
                return [], f"❌ 不允许的 find 动作: {token}"

        path_indexes = []
        for index, token in enumerate(parts[1:], start=1):
            if token.startswith('-') or token in {'!', '(', ')'}:
                break
            path_indexes.append(index)

        if not path_indexes:
            return ['find', '.'] + parts[1:], ""

        return self._replace_path_args(parts, path_indexes)

    def _validate_command_options(self, command: str, parts: List[str]) -> str:
        if command in {'grep', 'egrep', 'fgrep'}:
            for token in parts[1:]:
                if token.startswith('--file=') or (token.startswith('-f') and token != '-f'):
                    return "❌ grep 的 -f/--file 参数必须使用独立的工作目录内文件路径"

        if command == 'sort':
            for token in parts[1:]:
                if token == '-o' or token.startswith('-o') or token.startswith('--output'):
                    return "❌ sort 不允许写入输出文件"

        if command == 'tree':
            for token in parts[1:]:
                if token == '-o' or token.startswith('-o'):
                    return "❌ tree 不允许写入输出文件"

        return ""

    def _replace_path_args(self, parts: List[str], path_indexes: List[int]) -> Tuple[List[str], str]:
        path_index_set = set(path_indexes)
        safe_parts = []

        for index, token in enumerate(parts):
            if index not in path_index_set:
                safe_parts.append(token)
                continue

            expanded, error = self._expand_workspace_path(token)
            if error:
                return [], error
            safe_parts.extend(expanded)

        return safe_parts, ""

    def _path_argument_indexes(self, command: str, parts: List[str]) -> List[int]:
        """返回需要按文件路径校验的参数位置。"""
        if command in {'cat', 'file', 'stat', 'du', 'wc', 'sort', 'uniq'}:
            return self._non_option_indexes(parts, start=1)

        if command in {'ls', 'dir', 'tree'}:
            return self._non_option_indexes(parts, start=1)

        if command in {'head', 'tail', 'cut'}:
            return self._non_option_indexes(parts, start=1, skip_option_values=True)

        if command in {'grep', 'egrep', 'fgrep'}:
            return self._grep_path_indexes(parts)

        return []

    def _non_option_indexes(
        self,
        parts: List[str],
        start: int,
        skip_option_values: bool = False
    ) -> List[int]:
        indexes = []
        skip_next = False

        for index, token in enumerate(parts[start:], start=start):
            if skip_next:
                skip_next = False
                continue

            if token == '--':
                indexes.extend(range(index + 1, len(parts)))
                break

            if token.startswith('-') and token != '-':
                if skip_option_values and token in self.PATH_OPTION_VALUE_FLAGS:
                    skip_next = True
                continue

            indexes.append(index)

        return indexes

    def _grep_path_indexes(self, parts: List[str]) -> List[int]:
        indexes = []
        pattern_seen = False
        skip_next = False

        for index, token in enumerate(parts[1:], start=1):
            if skip_next:
                skip_next = False
                continue

            if token == '--':
                if not pattern_seen and index + 1 < len(parts):
                    pattern_seen = True
                    indexes.extend(range(index + 2, len(parts)))
                else:
                    indexes.extend(range(index + 1, len(parts)))
                break

            if token.startswith('-') and token != '-':
                if token in self.GREP_FILE_OPTION_VALUE_FLAGS:
                    if index + 1 < len(parts):
                        indexes.append(index + 1)
                    pattern_seen = True
                    skip_next = True
                    continue

                if token in {'-e', '--regexp'}:
                    pattern_seen = True
                    skip_next = True
                    continue

                if token.startswith('--regexp='):
                    pattern_seen = True
                    continue

                if token in self.GREP_OPTION_VALUE_FLAGS:
                    skip_next = True
                continue

            if not pattern_seen:
                pattern_seen = True
                continue

            indexes.append(index)

        return indexes

    def _expand_workspace_path(self, value: str) -> Tuple[List[str], str]:
        if any(char in value for char in '*?['):
            parent_text = str(Path(value).parent)
            pattern = Path(value).name
            parent, error = self._resolve_workspace_path(parent_text)
            if error:
                return [], error

            matches = sorted(parent.glob(pattern))
            if not matches:
                return [value], ""

            expanded = []
            for match in matches:
                resolved, error = self._resolve_workspace_path(str(match))
                if error:
                    return [], error
                expanded.append(str(resolved))
            return expanded, ""

        resolved, error = self._resolve_workspace_path(value)
        if error:
            return [], error
        return [str(resolved)], ""

    def _resolve_workspace_path(self, value: str) -> Tuple[Path, str]:
        if value == "~":
            resolved = self.workspace
        else:
            candidate = Path(value)
            if not candidate.is_absolute():
                candidate = self.current_dir / candidate
            resolved = candidate.resolve()

        try:
            resolved.relative_to(self.workspace)
        except ValueError:
            return resolved, f"❌ 不允许访问工作目录外的路径: {resolved}"

        return resolved, ""

    def _execute_command(self, parts: List[str]) -> str:
        """执行命令"""
        try:
            # 在当前目录下执行命令
            result = subprocess.run(
                parts,
                shell=False,
                cwd=str(self.current_dir),
                capture_output=True,
                stdin=subprocess.DEVNULL,
                text=True,
                timeout=self.timeout,
                env=os.environ.copy()
            )

            # 合并标准输出和标准错误
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"

            # 检查输出大小
            if len(output) > self.max_output_size:
                output = output[:self.max_output_size]
                output += f"\n\n⚠️ 输出被截断（超过 {self.max_output_size} 字节）"

            # 添加返回码信息
            if result.returncode != 0:
                output = f"⚠️ 命令返回码: {result.returncode}\n\n{output}"

            log.info(f"⛰️ [TerminalTool] [exec] final_output={output}")
            return output if output else "✅ 命令执行成功（无输出）"

        except subprocess.TimeoutExpired:
            log.error(f"❌ 命令执行超时（超过 {self.timeout} 秒）")
            return f"❌ 命令执行超时（超过 {self.timeout} 秒）"
        except Exception as e:
            log.error(f"❌ 命令执行失败: {e}")
            return f"❌ 命令执行失败: {e}"

    def get_current_dir(self) -> str:
        """获取当前工作目录"""
        return str(self.current_dir)

    def reset_dir(self):
        """重置到工作目录根"""
        self.current_dir = self.workspace
