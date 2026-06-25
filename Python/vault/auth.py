import os
import json
import secrets
from typing import Optional

try:
    from argon2.low_level import hash_secret_raw, Type
except Exception:
    hash_secret_raw = None
    Type = None

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
VAULT_FILE = os.path.join(DATA_DIR, "vault.json")

ERROR_CODE_VAULT_ALREADY_INITIALIZED = "E100"
ERROR_CODE_VAULT_NOT_INITIALIZED = "E101"
ERROR_CODE_INVALID_PASSWORD = "E102"
ERROR_CODE_CRYPTO_MISSING = "E103"
ERROR_CODE_KEY_DERIVATION_FAILED = "E104"
ERROR_CODE_GENERAL_FAILURE = "E199"


class AuthError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self):
        return f"[{self.code}] {self.message}"


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def is_initialized() -> bool:
    return os.path.exists(VAULT_FILE)


def initialize(
    password: str,
    *,
    time_cost: int = 2,
    memory_cost: int = 102400,
    parallelism: int = 8,
    hash_len: int = 32,
):
    _ensure_data_dir()
    if is_initialized():
        raise AuthError(
            ERROR_CODE_VAULT_ALREADY_INITIALIZED, "Vault already initialized"
        )
    if hash_secret_raw is None:
        raise AuthError(
            ERROR_CODE_CRYPTO_MISSING, "Argon2 is not available; install argon2-cffi"
        )

    salt = secrets.token_bytes(16)
    raw = hash_secret_raw(
        password.encode("utf-8"),
        salt,
        time_cost,
        memory_cost,
        parallelism,
        hash_len,
        Type.ID,
    )
    payload = {
        "salt": salt.hex(),
        "key": raw.hex(),
        "algo": "argon2id",
        "time_cost": time_cost,
        "memory_cost": memory_cost,
        "parallelism": parallelism,
        "hash_len": hash_len,
    }
    with open(VAULT_FILE, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)


def _derive_key(password: str) -> Optional[bytes]:
    if not is_initialized():
        return None
    with open(VAULT_FILE, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    algo = payload.get("algo")
    if algo != "argon2id" or hash_secret_raw is None:
        return None
    salt = bytes.fromhex(payload.get("salt"))
    time_cost = payload.get("time_cost", 2)
    memory_cost = payload.get("memory_cost", 102400)
    parallelism = payload.get("parallelism", 8)
    hash_len = payload.get("hash_len", 32)
    raw = hash_secret_raw(
        password.encode("utf-8"),
        salt,
        time_cost,
        memory_cost,
        parallelism,
        hash_len,
        Type.ID,
    )
    return raw


def verify_password(password: str) -> bool:
    if not is_initialized():
        raise AuthError(
            ERROR_CODE_VAULT_NOT_INITIALIZED, "Vault has not been initialized"
        )
    key = _derive_key(password)
    if key is None:
        raise AuthError(ERROR_CODE_KEY_DERIVATION_FAILED, "Unable to derive vault key")
    with open(VAULT_FILE, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    expected = payload.get("key")
    if not secrets.compare_digest(key.hex(), expected):
        raise AuthError(ERROR_CODE_INVALID_PASSWORD, "Incorrect password")
    return True


def verify(password: str) -> bool:
    try:
        return verify_password(password)
    except AuthError:
        return False


def get_db_key_hex(password: str) -> Optional[str]:
    key = _derive_key(password)
    if key is None:
        return None
    return key.hex()


if __name__ == "__main__":
    pass
