import os
import threading
from time import sleep
from collections import deque

import psutil
import resource

def get_process():
    return psutil.Process(os.getpid())

class UsageMonitoringThread(threading.Thread):
    def __init__(self, name: str, process: psutil.Process = None) -> None:
        self._stop_event = threading.Event()
        self._sleep_period = .0005
        self.result = None
        self.process = process
        super().__init__(name=name)
    
    def run(self):
        while not self._stop_event.is_set():
            ...
    
    def get_measurement(self, timeout=None) -> object:
        self._stop_event.set()
        super().join(timeout)
        return self.result
    

class CPUUsageMonitor(UsageMonitoringThread):
    def __init__(self, name: str = 'CPU Usage Monitor', process: psutil.Process = None) -> None:
        super().__init__(name, process)

    def run(self):
        if self.process is None:
            self.process = get_process()
        start = self.process.cpu_percent()
        measurements = deque(maxlen=10)
        while not self._stop_event.is_set():
            sleep(self._sleep_period)
            measurements.append(self.process.cpu_percent())
        self.result = max(measurements) - start if len(measurements) != 0 else 0


class MemoryUsageMonitor(UsageMonitoringThread):
    def __init__(self, name: str = 'RAM Usage Monitor', process: psutil.Process = None) -> None:
        super().__init__(name, process)

    def run(self):
        if self.process is None:
            self.process = get_process()
        start = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        measurements = deque(maxlen=10)
        while not self._stop_event.is_set():
            sleep(self._sleep_period)
            measurements.append(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        self.result = max(measurements) - start if len(measurements) != 0 else 0
