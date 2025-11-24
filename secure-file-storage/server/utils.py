# utils.py
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def gen_dek():
    return AESGCM.generate_key(bit_length=256)

def encrypt_bytes(dek: bytes, plaintext: bytes):
    aes = AESGCM(dek)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext, None)
    return nonce + ct

def decrypt_bytes(dek: bytes, blob: bytes):
    aes = AESGCM(dek)
    nonce = blob[:12]
    ct = blob[12:]
    return aes.decrypt(nonce, ct, None)
