"""Encrypt the project .env to env_tools/.env_encrypt."""

from getpass import getpass
from pathlib import Path
import sys

from env_crypto import EnvCryptoError, encrypt_file

TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TOOLS_DIR.parent


def main() -> int:
    password = getpass("请输入加密密码: ")
    confirmation = getpass("请再次输入加密密码: ")
    if password != confirmation:
        print("加密失败: 两次输入的密码不一致", file=sys.stderr)
        return 1

    try:
        encrypt_file(PROJECT_DIR / ".env", TOOLS_DIR / ".env_encrypt", password)
    except EnvCryptoError as exc:
        print(f"加密失败: {exc}", file=sys.stderr)
        return 1

    print("加密成功: 已将 .env 覆盖写入 env_tools/.env_encrypt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
