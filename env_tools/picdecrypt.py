"""Decrypt an image from env_tools/file/<name>.txt to the project directory."""

import sys
from pathlib import Path

from pic_crypto import PicCryptoError, decrypt_file


TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TOOLS_DIR.parent
FILE_DIR = TOOLS_DIR / "file"


def main() -> int:
    if len(sys.argv) != 3:
        print("用法: picdecrypt.py <密码> <原图片文件名>")
        return 1

    password = sys.argv[1]
    filename = sys.argv[2]
    txt_path = FILE_DIR / (Path(filename).stem + ".txt")
    out_path = PROJECT_DIR / Path(filename).name

    if not txt_path.exists():
        print(f"加密文件不存在: {txt_path}", file=sys.stderr)
        return 1

    try:
        decrypt_file(txt_path, out_path, password)
        print(f"解密成功: {txt_path} -> {out_path}")
    except PicCryptoError as exc:
        print(f"解密失败: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())