from __future__ import annotations
from config import config


class FieldCipher:
    PREFIX='enc:v1:'
    def __init__(self,key=None): self.key=key or config.FIELD_ENCRYPTION_KEY; self._cipher=None
    def _get(self):
        if not self.key: return None
        if self._cipher is None:
            from cryptography.fernet import Fernet
            self._cipher=Fernet(self.key.encode())
        return self._cipher
    def encrypt(self,value):
        if value is None or str(value).startswith(self.PREFIX): return value
        cipher=self._get()
        return self.PREFIX+cipher.encrypt(str(value).encode()).decode() if cipher else value
    def decrypt(self,value):
        if value is None or not str(value).startswith(self.PREFIX): return value
        cipher=self._get()
        return cipher.decrypt(str(value)[len(self.PREFIX):].encode()).decode() if cipher else '[encrypted]'
