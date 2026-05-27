#!/bin/bash

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TOOLS_DIR="$SCRIPT_DIR/env_tools"
FILE_DIR="$TOOLS_DIR/file"

mkdir -p "$FILE_DIR"

usage() {
    printf '用法: %s [encrypt|decrypt]\n' "$0" >&2
}

choose_action() {
    while true; do
        printf '%s\n' '请选择操作:' >&2
        printf '%s\n' '  1) 加密图片 -> env_tools/file/<文件名>.txt' >&2
        printf '%s\n' '  2) 解密图片 -> 当前目录' >&2
        printf '请输入选项 [1/2]: ' >&2
        read -r choice

        case "$choice" in
            1) echo "encrypt"; return 0 ;;
            2) echo "decrypt"; return 0 ;;
            *) printf '%s\n' '无效选项，请重新选择' >&2 ;;
        esac
    done
}

choose_file() {
    while true; do
        printf '%s' '请输入文件路径: ' >&2
        read -r filepath

        if [ -z "$filepath" ]; then
            printf '%s\n' '文件路径不能为空，请重新输入' >&2
            continue
        fi

        if [ ! -e "$filepath" ]; then
            printf '%s\n' "文件不存在: $filepath，请重新输入" >&2
            continue
        fi

        echo "$filepath"
        return 0
    done
}

choose_password() {
    while true; do
        printf '%s' '请输入密码: ' >&2
        read -r password

        if [ -z "$password" ]; then
            printf '%s\n' '密码不能为空，请重新输入' >&2
            continue
        fi

        echo "$password"
        return 0
    done
}

choose_password_confirm() {
    while true; do
        printf '%s' '请再次输入密码: ' >&2
        read -r password2

        if [ "$password" != "$password2" ]; then
            printf '%s\n' '两次输入的密码不一致，请重新输入' >&2
            continue
        fi

        echo "$password"
        return 0
    done
}

action=${1:-}
if [ -z "$action" ]; then
    action=$(choose_action)
fi

case "$action" in
    encrypt)
        echo '===== 加密图片 =====' >&2

        filepath=$(choose_file)
        password=$(choose_password)
        _=$(choose_password_confirm)

        filename=$(basename -- "$filepath")
        txt_name="${filename%.*}.txt"
        txt_path="$FILE_DIR/$txt_name"

        printf '\n%s\n' "加密: $filepath -> $txt_path" >&2
        python "$TOOLS_DIR/picencrypt.py" -e "$password" "$filepath"
        ;;

    decrypt)
        echo '===== 解密图片 =====' >&2

        while true; do
            printf '%s' '请输入原图片文件名: ' >&2
            read -r filename

            if [ -z "$filename" ]; then
                printf '%s\n' '文件名不能为空，请重新输入' >&2
                continue
            fi
            break
        done

        txt_name="${filename%.*}.txt"
        txt_path="$FILE_DIR/$txt_name"

        if [ ! -e "$txt_path" ]; then
            printf '%s\n' "加密文件不存在: $txt_path" >&2
            exit 1
        fi

        password=$(choose_password)

        out_path="$SCRIPT_DIR/$filename"
        printf '\n%s\n' "解密: $txt_path -> $out_path" >&2
        python "$TOOLS_DIR/picdecrypt.py" "$password" "$filename"
        ;;

    *)
        usage
        exit 1
        ;;
esac