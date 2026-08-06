"""SHUNYA OS — Encryption at Rest (Fernet).

Uses the cryptography Fernet symmetric encryption scheme.
The key is derived from the Flask app's SECRET_KEY, ensuring
zero additional infrastructure or paid services.

Usage:
    from app.security.encryption import encrypt_value, decrypt_value

    encrypted = encrypt_value("sensitive@email.com")
    decrypted = decrypt_value(encrypted)
"""

from base64 import b64encode, b64decode

from cryptography.fernet import Fernet


def _get_fernet():
    """Get a Fernet instance derived from the Flask app's SECRET_KEY."""
    from flask import current_app

    secret = current_app.config["SECRET_KEY"].encode()[:32]
    secret = secret.ljust(32, b"\0")
    key = b64encode(secret)
    return Fernet(key)


def encrypt_value(value: str) -> str:
    """Encrypt a plaintext string using Fernet (symmetric encryption)."""
    f = _get_fernet()
    return f.encrypt(value.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    """Decrypt a Fernet-encrypted string back to plaintext."""
    f = _get_fernet()
    return f.decrypt(encrypted.encode()).decode()