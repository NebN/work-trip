import time
from threading import Timer
from src.log import logging


class ScheduledTask:
    """
    Non blocking scheduler inspired by https://stackoverflow.com/a/38317060/6142754
    """
    def __init__(self, task, timedelta, *args, **kwargs):
        self.task = task
        self.interval_in_seconds = timedelta.total_seconds()
        self.args = args
        self.kwargs = kwargs
        self._timer = None
        self._logger = logging.get_logger(__name__)

    def _run(self):
        t0 = time.process_time()
        self.task(*self.args, **self.kwargs)
        time_taken = (time.process_time() - t0)
        self._logger.debug('time taken to execute %s: %s', self.task.__name__, time_taken)
        next_call_delay = max(0, self.interval_in_seconds - time_taken)
        self.start(next_call_delay)

    def start(self, delay_in_seconds=None):
        wait_time = delay_in_seconds if delay_in_seconds else self.interval_in_seconds
        self._timer = Timer(wait_time, self._run)
        self._logger.debug('next call in %s seconds', wait_time)
        try:
            self._timer.start()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self._timer.cancel()
        self._logger.debug('stopping execution of %s', self.task.__name__)
