from abc import ABC, abstractmethod
from typing import Tuple
from time import time
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding

import oqs

from .utils import CURVE_MAP

Plaintext = bytes
Ciphertext = bytes
KeyPair = Tuple[bytes, bytes]

class KEMRunner(ABC):
    def __init__(self, algorithm: str, variant: str) -> None:
        self.algorithm = algorithm
        self.variant = variant

    @abstractmethod
    def generate_key(self) -> KeyPair:
        ...

    @abstractmethod
    def encrypt(self, public_key: bytes, plaintext: Plaintext) -> Ciphertext:
        ...
    
    @abstractmethod
    def decrypt(self, secret_key: bytes, ciphertext: Ciphertext) -> Plaintext:
        ...


class OQSKEMRunner(KEMRunner):
    def __init__(self, algorithm: str, variant: str) -> None:
        super().__init__(algorithm, variant)
        self.system = f"{algorithm}-{variant}"

    def generate_key(self) -> KeyPair:
        with oqs.KeyEncapsulation(self.system) as client:
            start = time()
            public_key = client.generate_keypair()
            secret_key = client.export_secret_key()
            end = time()
        self.keygen_time = end - start
        return public_key, secret_key
    
    def encrypt(self, public_key: bytes, plaintext: Plaintext) -> Ciphertext:
        # TODO Encrypt *this* plaintext
        with oqs.KeyEncapsulation(self.system) as client:
            start = time()
            ciphertext, _ = client.encap_secret(public_key)
            end = time()
        self.encrypt_time = end - start
        return ciphertext
    
    def decrypt(self, secret_key: bytes, ciphertext: Ciphertext) -> Plaintext:
        with oqs.KeyEncapsulation(self.system, secret_key) as client:
            start = time()
            plaintext = client.decap_secret(ciphertext)
            end = time()
        self.decrypt_time = end - start
        return plaintext

class RSAKEMRunner(KEMRunner):
    HASH = hashes.SHA256()
    PADDING = padding.OAEP(mgf=padding.MGF1(algorithm=HASH), algorithm=HASH, label=None)

    def generate_key(self) -> KeyPair:
        start = time()
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=int(self.variant)
        )
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_key = private_key.public_key()
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        end = time()
        self.keygen_time = end - start
        return public_key_bytes,  private_key_bytes

    def encrypt(self, public_key: bytes, plaintext: Plaintext) -> Ciphertext:
        start = time()
        public_key_loaded = serialization.load_pem_public_key(public_key)
        ciphertext = public_key_loaded.encrypt(plaintext, padding=self.PADDING)
        end = time()
        self.encrypt_time = end - start
        return ciphertext
    
    def decrypt(self, secret_key: bytes, ciphertext: Ciphertext) -> Plaintext:
        start = time()
        private_key_loaded = serialization.load_pem_private_key(secret_key, password=None)
        plaintext = private_key_loaded.decrypt(ciphertext, padding=self.PADDING)
        end = time()
        self.decrypt_time = end - start
        return plaintext

class ECCKEMRunner(RSAKEMRunner):
    def generate_key(self) -> KeyPair:
        curve = CURVE_MAP[self.variant]
        private_key = ec.generate_private_key(curve)
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_key = private_key.public_key()
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return public_key_bytes,  private_key_bytes
