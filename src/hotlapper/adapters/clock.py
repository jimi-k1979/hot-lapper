import time

from hotlapper.application.ports import Seconds


class PerfCounterClock:
    def now(self) -> Seconds:
        return time.perf_counter()
