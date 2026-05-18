import os
import base64
from cryptography.fernet import Fernet

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'news_aggregator.db')}"
KEY_FILE = os.path.join(BASE_DIR, ".encryption_key")


def get_or_create_encryption_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    return key


def encrypt_value(plaintext: str) -> str:
    key = get_or_create_encryption_key()
    f = Fernet(key)
    return base64.b64encode(f.encrypt(plaintext.encode())).decode()


def decrypt_value(ciphertext: str) -> str:
    key = get_or_create_encryption_key()
    f = Fernet(key)
    return f.decrypt(base64.b64decode(ciphertext.encode())).decode()
