from abc import ABC, abstractmethod
from typing import Tuple
from time import time

import pandas as pd
import numpy as np
from numpy import random

from oqs_bench.runners.kem import ECCKEMRunner, OQSKEMRunner, RSAKEMRunner
from oqs_bench.runners.sign import OQSSignRunner, RSASignRunner

from .monitors import MemoryUsageMonitor, get_process

KEM_RUNNERS = {
    'OQS': OQSKEMRunner,
    'RSA': RSAKEMRunner,
    'ECC': ECCKEMRunner
}

SIG_RUNNERS = {
    'RSA': RSASignRunner,
    'OQS': OQSSignRunner
}

class TestRunner(ABC):
    PS_THRESH = 10
    X = 500

    def __init__(self, algorithm: str, variant: str):
        self.algorithm = algorithm
        self.variant = variant
        self.process = get_process()
    
    def _monitor_crypto_func(self, func, *args) -> Tuple[object, float]:
        # Init monitors
        memory_monitor = MemoryUsageMonitor(process=self.process)
        memory_monitor.start()

        # Output
        result = func(*args)

        # Measurements
        memory_usage = memory_monitor.get_measurement()

        return result, memory_usage

    def _bench_per_second(self, func, *args) -> float:
        original_time_s = time()
        current_time_s = original_time_s
        count = 0
        while current_time_s < original_time_s + self.PS_THRESH:
            _ = func(*args)
            count += 1
            current_time_s = time()
        return count / float(self.PS_THRESH)

    @abstractmethod
    def test(self) -> pd.DataFrame:
        ...

class KEMTestRunner(TestRunner):
    def __init__(self, algorithm: str, variant: str, runner: str):
        super().__init__(algorithm, variant)
        self.runner = KEM_RUNNERS[runner](algorithm, variant)
    
    def test(self) -> pd.DataFrame:
        # Keygen
        keygen_times = np.zeros(self.X)
        keygen_memory_usages = np.zeros(self.X)
        for i in range(self.X):
            keypair, keygen_memory_usage = self._monitor_crypto_func(self.runner.generate_key)
            keygen_times[i] = self.runner.keygen_time
            keygen_memory_usages[i] = keygen_memory_usage
        keygen_time_mean = keygen_times.mean()
        keygen_time_std_div = keygen_times.std()
        keygen_memory_usage_max = keygen_memory_usages.max()
        pubkey_length = len(keypair[0])
        secretkey_length = len(keypair[1])

        # Encapsulate
        encaps_times = np.zeros(self.X)
        encaps_memory_usages = np.zeros(self.X)
        for i in range(self.X):
            (ciphertext, shared_secret), encaps_memory_usage = self._monitor_crypto_func(self.runner.encapsulate, keypair[0])
            encaps_times[i] =  self.runner.encrypt_time
            encaps_memory_usages[i] = encaps_memory_usage
        encaps_time_mean = encaps_times.mean()
        encaps_time_std_div = encaps_times.std()
        encaps_memory_usage_max = encaps_memory_usages.max()
        ciphertext_length = len(ciphertext)
        decapsulations_per_second = self._bench_per_second(self.runner.encapsulate, keypair[0])

        # Decrypt
        decaps_times = np.zeros(self.X)
        decaps_memory_usages = np.zeros(self.X)
        for i in range(self.X):
            shared_secret_2, decaps_memory_usage = self._monitor_crypto_func(self.runner.decapsulate, keypair[1], ciphertext)
            decaps_times[i] = self.runner.decrypt_time
            decaps_memory_usages[i] = decaps_memory_usage
        decaps_time_mean = decaps_times.mean()
        decaps_time_std_div = decaps_times.std()
        decaps_memory_usage_max = decaps_memory_usages.max()
        decapsulations_per_second = self._bench_per_second(self.runner.decapsulate, keypair[1], ciphertext)
        assert shared_secret_2 == shared_secret
            

        return pd.DataFrame({
            'Mean Keygen Time': keygen_time_mean,
            'Keygen Time Standard Deviation': keygen_time_std_div,
            'Maximum Keygen Memory Usage': keygen_memory_usage_max,
            'Mean Encapsulation Time': encaps_time_mean,
            'Encapsulation Time Standard Deviation': encaps_time_std_div,
            'Maximum Encapsulation Memory Usage': encaps_memory_usage_max,
            'Encapsulations Per Second': decapsulations_per_second,
            'Mean Decapsulation Time': decaps_time_mean,
            'Decapsulation Time Standard Deviation': decaps_time_std_div,
            'Maximum Decapsulation Memory Usage': decaps_memory_usage_max,
            'Decapsulations Per Second': decapsulations_per_second,
            'Public Key length': pubkey_length,
            'Secret Key length': secretkey_length,
            'Ciphertext length': ciphertext_length,
        }, index=[self.variant])


class SignTestRunner(TestRunner):
    def __init__(self, algorithm: str, variant: str, runner: str):
        super().__init__(algorithm, variant)
        self.runner = SIG_RUNNERS[runner](algorithm, variant)
    
    def test(self) -> pd.DataFrame:
        # Keygen
        keygen_times = np.zeros(self.X)
        keygen_memory_usages = np.zeros(self.X)
        for i in range(self.X):
            keypair, keygen_memory_usage = self._monitor_crypto_func(self.runner.generate_key)
            keygen_times[i] = self.runner.keygen_time
            keygen_memory_usages[i] = keygen_memory_usage
        keygen_time_mean = keygen_times.mean()
        keygen_time_std_div = keygen_times.std()
        keygen_memory_usage_max = keygen_memory_usages.max()
        pubkey_length = len(keypair[0])
        secretkey_length = len(keypair[1])

        # Sign
        plaintext = random.bytes(64)
        sign_times = np.zeros(self.X)
        sign_memory_usages = np.zeros(self.X)
        for i in range(self.X):
            signature, sign_memory_usage = self._monitor_crypto_func(self.runner.sign, keypair[1], plaintext)
            sign_times[i] = self.runner.sign_time
            sign_memory_usages[i] = sign_memory_usage
        sign_time_mean = sign_times.mean()
        sign_time_std_div = sign_times.std()
        sign_memory_usage_max = sign_memory_usages.max()
        signature_length = len(signature)
        signatures_per_second = self._bench_per_second(self.runner.sign, keypair[1], plaintext)

        # Verify
        verify_times = np.zeros(self.X)
        verify_memory_usages = np.zeros(self.X)
        for i in range(self.X):
            verified, verify_memory_usage = self._monitor_crypto_func(self.runner.verify, keypair[0], plaintext, signature)
            verify_times[i] = self.runner.verify_time
            verify_memory_usages[i] = verify_memory_usage
        verify_time_mean = verify_times.mean()
        verify_time_std_div = verify_times.std()
        verify_memory_usage_max = verify_memory_usages.max()
        verifications_per_second = self._bench_per_second(self.runner.verify, keypair[0], plaintext, signature)
        # assert verified

        return pd.DataFrame({
            'Mean Keygen Time': keygen_time_mean,
            'Keygen Time Standard Deviation': keygen_time_std_div,
            'Maximum Keygen Memory Usage': keygen_memory_usage_max,
            'Mean Encapsulation Time': sign_time_mean,
            'Encapsulation Time Standard Deviation': sign_time_std_div,
            'Maximum Keygen Memory Usage': sign_memory_usage_max,
            'Signatures Per Second': signatures_per_second,
            'Mean Verification Time': verify_time_mean,
            'Verification Time Standard Deviation': verify_time_std_div,
            'Maximum Verification Memory Usage': verify_memory_usage_max,
            'Verifications Per Second': verifications_per_second,
            'Public Key length': pubkey_length,
            'Secret Key length': secretkey_length,
            'Signature length': signature_length,
        }, index=[self.variant])
