"""
Crypto helpers for payload encryption.

This module provides a Windows-friendly alternative to SQLCipher by encrypting
sensitive payloads (note content, attachments) at the application layer.
"""

import base64
from cryptography.fernet import Fernet


def _make_fernet(key_hex: str) -> Fernet:
    key = bytes.fromhex(key_hex)
    if len(key) < 32:
        raise ValueError("Derived key must be at least 32 bytes")
    return Fernet(base64.urlsafe_b64encode(key[:32]))


def encrypt_bytes(b: bytes, key_hex: str) -> bytes:
    return _make_fernet(key_hex).encrypt(b)


def decrypt_bytes(b: bytes, key_hex: str) -> bytes:
    return _make_fernet(key_hex).decrypt(b)


if __name__ == "__main__":
    pass
