from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

class StandPyCipher:
    START_KEY = b"key_abcdefghijkl"
    START_IV  = b"iv_abcdefghijklm"

    def __init__(self):
        self._key = StandPyCipher.START_KEY
        self._iv = StandPyCipher.START_IV
        self._cipher = self._make(self._key, self._iv)

    def _make(self, key, iv):
        return Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )

    def new_aes_cipher(self, key: bytes, iv: bytes):
        self._key = key
        self._iv = iv
        self._cipher = self._make(key, iv)

    def encrypt(self, data: bytes) -> bytes:
        encryptor = self._cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded = padder.update(data) + padder.finalize()
        return encryptor.update(padded) + encryptor.finalize()

    def decrypt(self, data: bytes) -> bytes:
        decryptor = self._cipher.decryptor()
        raw = decryptor.update(data) + decryptor.finalize()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        return unpadder.update(raw) + unpadder.finalize()
