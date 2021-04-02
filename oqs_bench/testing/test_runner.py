from abc import ABC

from oqs_bench.runners import KEMRunner, SignRunner
from .monitors import CPUUsageMonitor, MemoryUsageMonitor, get_process

class TestRunner(ABC):
    def __init__(self, algorithm: str, variant: str):
        self.algorithm = algorithm
        self.variant = variant
        process = get_process()
        self.cpu_monitor = CPUUsageMonitor(process=process)
        self.memory_monitor = MemoryUsageMonitor(process=process)

class KEMTestRunner(TestRunner):
    def __init__(self, algorithm: str, variant: str):
        super().__init__(algorithm, variant)
        self.runner = KEMRunner(algorithm, variant)
    
    def test_keygen(self):
        # Init monitors
        self.cpu_monitor.start()
        self.memory_monitor.start()

        # Output
        keypair = self.runner.generate_key()
        
        # Measurements
        cpu_usage = self.cpu_monitor.get_measurement()
        memory_usage = self.memory_monitor.get_measurement()
        keygen_time = self.runner.keygen_time
        pubkey_length = len(keypair[0])
        secretkey_length = len(keypair[1])
