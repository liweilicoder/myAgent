#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

usage() {
    printf '用法: %s [encrypt|decrypt]\n' "$0" >&2
}

choose_action() {
    printf '%s\n' '请选择操作:' >&2
    printf '%s\n' '  1) 加密 .env -> env_tools/.env_encrypt' >&2
    printf '%s\n' '  2) 解密 env_tools/.env_encrypt -> .env' >&2
    printf '请输入选项 [1/2]: ' >&2
    IFS= read -r choice

    case "$choice" in
        1) printf '%s\n' encrypt ;;
        2) printf '%s\n' decrypt ;;
        *)
            printf '%s\n' '无效选项，操作已取消' >&2
            exit 1
            ;;
    esac
}

action=${1:-}
if [ -z "$action" ]; then
    action=$(choose_action)
fi

case "$action" in
    encrypt)
        target=env_tools/encrypt.py
        ;;
    decrypt)
        target=env_tools/decrypt.py
        ;;
    *)
        usage
        exit 1
        ;;
esac

if ! command -v uv >/dev/null 2>&1; then
    printf '%s\n' '运行失败: 未找到 uv，请先安装项目依赖管理工具 uv' >&2
    exit 1
fi

cd "$SCRIPT_DIR"
# This tool uses dependencies locked for this project, independent of a caller's active venv.
exec env -u VIRTUAL_ENV uv run python "$target"
