"""Password-based authenticated encryption for local environment files."""

from __future__ import annotations

import base64
import binascii
import json
import os
from pathlib import Path
import tempfile

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


class EnvCryptoError(Exception):
    """Raised when an environment file cannot be encrypted or decrypted."""


_HEADER = {
    "format": "myagent-env",
    "version": 1,
    "cipher": "AES-256-GCM",
    "kdf": {
        "name": "scrypt",
        "length": 32,
        "n": 2**15,
        "r": 8,
        "p": 1,
    },
}
_ENVELOPE_KEYS = set(_HEADER) | {"salt", "nonce", "ciphertext"}
_SALT_LENGTH = 16
_NONCE_LENGTH = 12


def _header_bytes() -> bytes:
    return json.dumps(_HEADER, sort_keys=True, separators=(",", ":")).encode("ascii")


def _derive_key(password: str, salt: bytes) -> bytes:
    if not password:
        raise EnvCryptoError("密码不能为空")
    return Scrypt(
        salt=salt,
        length=_HEADER["kdf"]["length"],
        n=_HEADER["kdf"]["n"],
        r=_HEADER["kdf"]["r"],
        p=_HEADER["kdf"]["p"],
    ).derive(password.encode("utf-8"))


def _encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _decode(value: object, name: str) -> bytes:
    if not isinstance(value, str):
        raise EnvCryptoError(f"加密文件中的 {name} 字段无效")
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error) as exc:
        raise EnvCryptoError(f"加密文件中的 {name} 字段无效") from exc


def encrypt_bytes(plaintext: bytes, password: str) -> bytes:
    """Encrypt bytes into the versioned JSON envelope stored in .env_encrypt."""
    salt = os.urandom(_SALT_LENGTH)
    nonce = os.urandom(_NONCE_LENGTH)
    key = _derive_key(password, salt)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, _header_bytes())
    envelope = {
        **_HEADER,
        "salt": _encode(salt),
        "nonce": _encode(nonce),
        "ciphertext": _encode(ciphertext),
    }
    return (json.dumps(envelope, indent=2, sort_keys=True) + "\n").encode("ascii")


def decrypt_bytes(encrypted: bytes, password: str) -> bytes:
    """Decrypt a JSON envelope, rejecting wrong passwords or modified data."""
    try:
        envelope = json.loads(encrypted.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EnvCryptoError("加密文件格式无效") from exc

    if not isinstance(envelope, dict) or set(envelope) != _ENVELOPE_KEYS:
        raise EnvCryptoError("加密文件格式无效")
    if {key: envelope[key] for key in _HEADER} != _HEADER:
        raise EnvCryptoError("不支持的加密文件版本或算法")

    salt = _decode(envelope["salt"], "salt")
    nonce = _decode(envelope["nonce"], "nonce")
    ciphertext = _decode(envelope["ciphertext"], "ciphertext")
    if len(salt) != _SALT_LENGTH or len(nonce) != _NONCE_LENGTH:
        raise EnvCryptoError("加密文件参数无效")

    key = _derive_key(password, salt)
    try:
        return AESGCM(key).decrypt(nonce, ciphertext, _header_bytes())
    except InvalidTag as exc:
        raise EnvCryptoError("密码错误或加密文件已被篡改") from exc


def _atomic_write(path: Path, content: bytes) -> None:
    path = Path(path)
    if not path.parent.exists():
        raise EnvCryptoError(f"目标目录不存在: {path.parent}")

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            os.chmod(temp_path, 0o600)
            temp_file.write(content)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_path, path)
        temp_path = None
    except OSError as exc:
        raise EnvCryptoError(f"无法写入文件 {path}: {exc}") from exc
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def encrypt_file(source: Path, target: Path, password: str) -> None:
    """Read source and atomically overwrite target with encrypted contents."""
    try:
        plaintext = Path(source).read_bytes()
    except OSError as exc:
        raise EnvCryptoError(f"无法读取文件 {source}: {exc}") from exc
    _atomic_write(Path(target), encrypt_bytes(plaintext, password))


def decrypt_file(source: Path, target: Path, password: str) -> None:
    """Read source and atomically overwrite target only after authentication."""
    try:
        encrypted = Path(source).read_bytes()
    except OSError as exc:
        raise EnvCryptoError(f"无法读取文件 {source}: {exc}") from exc
    _atomic_write(Path(target), decrypt_bytes(encrypted, password))
