"""Decrypt env_tools/.env_encrypt to the project .env."""

from getpass import getpass
from pathlib import Path
import sys

from env_crypto import EnvCryptoError, decrypt_file

TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TOOLS_DIR.parent


def main() -> int:
    password = getpass("请输入解密密码: ")
    try:
        decrypt_file(TOOLS_DIR / ".env_encrypt", PROJECT_DIR / ".env", password)
    except EnvCryptoError as exc:
        print(f"解密失败: {exc}", file=sys.stderr)
        return 1

    print("解密成功: 已将 env_tools/.env_encrypt 覆盖写入 .env")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
