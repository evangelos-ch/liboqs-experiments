from abc import ABC, abstractmethod
from typing import Tuple

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding

import oqs

from .utils import CURVE_MAP, current_milli_time

Plaintext = bytes
Signature = bytes
KeyPair = Tuple[bytes, bytes]

class SignRunner(ABC):
    def __init__(self, algorithm: str, variant: str) -> None:
        self.algorithm = algorithm
        self.variant = variant

    @abstractmethod
    def generate_key(self) -> KeyPair:
        ...

    @abstractmethod
    def sign(self, secret_key: bytes, plaintext: Plaintext) -> Signature:
        ...
    
    @abstractmethod
    def verify(self, public_key: bytes, plaintext: Plaintext, signature: Signature) -> bool:
        ...


class OQSSignRunner(SignRunner):
    def __init__(self, algorithm: str, variant: str) -> None:
        super().__init__(algorithm, variant)
        self.system = variant

    def generate_key(self) -> KeyPair:
        with oqs.Signature(self.system) as signer:
            start = current_milli_time()
            public_key = signer.generate_keypair()
            secret_key = signer.export_secret_key()
            end = current_milli_time()
            self.keygen_time = end - start
        return public_key, secret_key
    
    def sign(self, secret_key: bytes, plaintext: Plaintext) -> Signature:
        with oqs.Signature(self.system, secret_key=secret_key) as signer:
            start = current_milli_time()
            signature = signer.sign(plaintext)
            end = current_milli_time()
            self.sign_time = end - start
        return signature
    
    def verify(self, public_key: bytes, plaintext: Plaintext, signature: Signature) -> bool:
        with oqs.Signature(self.system) as verifier:
            start = current_milli_time()
            valid = verifier.verify(plaintext, signature, public_key)
            end = current_milli_time()
            self.verify_time = end - start
        return valid


class RSASignRunner(SignRunner):
    HASH = hashes.SHA256()
    PADDING = padding.PSS(mgf=padding.MGF1(algorithm=HASH), salt_length=padding.PSS.MAX_LENGTH)

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

    def sign(self, secret_key: bytes, plaintext: Plaintext) -> Signature:
        start = current_milli_time()
        public_key_loaded = serialization.load_pem_private_key(secret_key, password=None)
        ciphertext = public_key_loaded.sign(plaintext, self.PADDING, self.HASH)
        end = current_milli_time()
        self.sign_time = end - start
        return ciphertext
    
    def verify(self, public_key: bytes, plaintext: Plaintext, signature: Signature) -> bool:
        start = current_milli_time()
        private_key_loaded = serialization.load_pem_public_key(public_key)
        valid = private_key_loaded.verify(signature, plaintext, self.PADDING, self.HASH)
        end = current_milli_time()
        self.verify_time = end - start
        return valid

class ECCSignRunner(RSASignRunner):
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
        return public_key_bytes, private_key_bytes

    def sign(self, secret_key: bytes, plaintext: Plaintext) -> Signature:
        start = current_milli_time()
        public_key_loaded = serialization.load_pem_private_key(secret_key, password=None)
        ciphertext = public_key_loaded.sign(plaintext, ec.ECDSA(self.HASH))
        end = current_milli_time()
        self.sign_time = end - start
        return ciphertext
    
    def verify(self, public_key: bytes, plaintext: Plaintext, signature: Signature) -> bool:
        start = current_milli_time()
        private_key_loaded = serialization.load_pem_public_key(public_key)
        valid = private_key_loaded.verify(signature, plaintext, ec.ECDSA(self.HASH))
        end = current_milli_time()
        self.verify_time = end - start
        return valid
