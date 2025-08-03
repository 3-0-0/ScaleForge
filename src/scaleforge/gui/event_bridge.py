import threading
import time
from kivy.clock import Clock
from scaleforge.pipeline.queue import JobQueue

class JobQueueObserver:
    def __init__(self, job_queue: JobQueue, update_callback):
        self.job_queue = job_queue
        self.update_callback = update_callback
        self._running = True
        self.thread = threading.Thread(target=self._monitor)
        self.thread.daemon = True
        self.thread.start()

    def _monitor(self):
        while self._running:
            if self.job_queue.has_updates():
                Clock.schedule_once(lambda dt: self.update_callback())
            time.sleep(0.5)  # Check twice per second

    def stop(self):
        self._running = False
        self.thread.join()
