import os
import threading
from time import sleep
from collections import deque

import psutil

def get_process():
    return psutil.Process(os.getpid())

class UsageMonitoringThread(threading.Thread):
    def __init__(self, name: str, process: psutil.Process = None) -> None:
        self._stopevent = threading.Event()
        self._sleepperiod = 1.0
        self.result = None
        self.process = process
        super().__init__(self, name=name)
    
    def run(self):
        while not self._stopevent.is_set():
            ...
    
    def get_measurement(self, timeout=None) -> object:
        self._stopevent.set()
        super().join(self, timeout)
        return self.result
    

class CPUUsageMonitor(UsageMonitoringThread):
    def __init__(self, name: str = 'CPU Usage Monitor', process: psutil.Process = None) -> None:
        super().__init__(name, process)

    def run(self):
        if self.process is None:
            self.process = get_process()
        start = self.process.cpu_percent()
        measurements = deque(maxlen=10)
        while not self._stopevent.is_set():
            measurements.append(self.process.cpu_percent())
            sleep(self._sleepperiod)
        self.result = max(measurements) - start


class MemoryUsageMonitor(UsageMonitoringThread):
    def __init__(self, name: str = 'RAM Usage Monitor', process: psutil.Process = None) -> None:
        super().__init__(name, process)

    def run(self):
        if self.process is None:
            self.process = get_process()
        start = self.process.memory_info()
        measurements = deque(maxlen=10)
        while not self._stopevent.is_set():
            measurements.append(self.process.memory_info())
            sleep(self._sleepperiod)
        self.result = max(measurements) - start
