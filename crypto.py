import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv


load_dotenv()

TOKEN_ENCRYPTION_KEY = os.getenv("TOKEN_ENCRYPTION_KEY")

if not TOKEN_ENCRYPTION_KEY:
    raise RuntimeError(
        "TOKEN_ENCRYPTION_KEY missing from .env. "
        "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    )

_fernet = Fernet(TOKEN_ENCRYPTION_KEY.encode())


def encrypt_str(plaintext: str) -> str:
    """Encrypt a string. Returns base64-encoded ciphertext."""
    if plaintext is None:
        return None
    ciphertext_bytes = _fernet.encrypt(plaintext.encode())
    return ciphertext_bytes.decode()


def decrypt_str(ciphertext: str) -> str:
    """Decrypt a string. Returns the original plaintext."""
    if ciphertext is None:
        return None
    plaintext_bytes = _fernet.decrypt(ciphertext.encode())
    return plaintext_bytes.decode()