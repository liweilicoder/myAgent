"""Encrypt an image file and store it in env_tools/file/<name>.txt."""

import sys
from pathlib import Path

from pic_crypto import PicCryptoError, encrypt_file


TOOLS_DIR = Path(__file__).resolve().parent
FILE_DIR = TOOLS_DIR / "file"


def main() -> int:
    if len(sys.argv) != 4 or sys.argv[1] not in ("-e", "-d"):
        print("用法: picencrypt.py -e <密码> <图片文件>")
        print("       picencrypt.py -d <密码> <图片文件>")
        return 1

    mode = sys.argv[1]
    password = sys.argv[2]
    image_path = Path(sys.argv[3]).resolve()

    if not image_path.exists():
        print(f"文件不存在: {image_path}", file=sys.stderr)
        return 1

    txt_name = image_path.stem + ".txt"
    txt_path = FILE_DIR / txt_name

    try:
        if mode == "-e":
            encrypt_file(image_path, txt_path, password)
            print(f"加密成功: {image_path} -> {txt_path}")
        else:  # -d
            decrypt_file(txt_path, image_path, password)
            print(f"解密成功: {txt_path} -> {image_path}")
    except PicCryptoError as exc:
        print(f"失败: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    from pic_crypto import decrypt_file
    raise SystemExit(main())