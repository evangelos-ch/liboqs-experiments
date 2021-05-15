from abc import ABC, abstractmethod
from typing import Tuple
from functools import cached_property

import oqs
import numpy as np
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding

from .utils import CURVE_MAP, current_milli_time

Plaintext = bytes
Ciphertext = bytes
SharedSecret = bytes
KeyPair = Tuple[bytes, bytes]

class KEMRunner(ABC):
    def __init__(self, algorithm: str, variant: str) -> None:
        self.algorithm = algorithm
        self.variant = variant

    @abstractmethod
    def generate_key(self) -> KeyPair:
        ...

    @abstractmethod
    def encapsulate(self, public_key: bytes) -> Tuple[Ciphertext, SharedSecret]:
        ...
    
    @abstractmethod
    def decapsulate(self, secret_key: bytes, ciphertext: Ciphertext) -> SharedSecret:
        ...


class OQSKEMRunner(KEMRunner):
    def __init__(self, algorithm: str, variant: str) -> None:
        super().__init__(algorithm, variant)
        self.system = variant

    def generate_key(self) -> KeyPair:
        with oqs.KeyEncapsulation(self.system) as client:
            start = current_milli_time()
            public_key = client.generate_keypair()
            secret_key = client.export_secret_key()
            end = current_milli_time()
        self.keygen_time = end - start
        return public_key, secret_key
    
    def encapsulate(self, public_key: bytes) -> Tuple[Ciphertext, SharedSecret]:
        with oqs.KeyEncapsulation(self.system) as client:
            start = current_milli_time()
            ciphertext, shared_secret = client.encap_secret(public_key)
            end = current_milli_time()
        self.encrypt_time = end - start
        return ciphertext, shared_secret
    
    def decapsulate(self, secret_key: bytes, ciphertext: Ciphertext) -> SharedSecret:
        with oqs.KeyEncapsulation(self.system, secret_key) as client:
            start = current_milli_time()
            plaintext = client.decap_secret(ciphertext)
            end = current_milli_time()
        self.decrypt_time = end - start
        return plaintext

class RSAKEMRunner(KEMRunner):
    HASH = hashes.SHA256()
    PADDING = padding.OAEP(mgf=padding.MGF1(algorithm=HASH), algorithm=HASH, label=None)

    @cached_property
    def SHARED_SECRET(self):
        return np.random.bytes(128)

    def generate_key(self) -> KeyPair:
        start = current_milli_time()
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
        end = current_milli_time()
        self.keygen_time = end - start
        return public_key_bytes,  private_key_bytes

    def encapsulate(self, public_key: bytes) -> Tuple[Ciphertext, SharedSecret]:
        start = current_milli_time()
        public_key_loaded = serialization.load_pem_public_key(public_key)
        ciphertext = public_key_loaded.encrypt(self.SHARED_SECRET, padding=self.PADDING)
        end = current_milli_time()
        self.encrypt_time = end - start
        return ciphertext, self.SHARED_SECRET
    
    def decapsulate(self, secret_key: bytes, ciphertext: Ciphertext) -> SharedSecret:
        start = current_milli_time()
        private_key_loaded = serialization.load_pem_private_key(secret_key, password=None)
        plaintext = private_key_loaded.decrypt(ciphertext, padding=self.PADDING)
        end = current_milli_time()
        self.decrypt_time = end - start
        return plaintext

class ECCKEMRunner(RSAKEMRunner):
    # TODO Fix this runner
    def generate_key(self) -> KeyPair:
        start = current_milli_time()
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
        end = current_milli_time()
        self.keygen_time = end - start
        return public_key_bytes,  private_key_bytes
