import logging
import queue
import threading
import time

logger = logging.getLogger("runtime_rca")


class EventWorker:

    def __init__(self, transport, max_queue_size=1000):
        self.transport = transport
        self.queue = queue.Queue(maxsize=max_queue_size)

        self.condition = threading.Condition()
        self.pending = 0
        self.accepting = True

        self.thread = threading.Thread(
            target=self._run,
            name="runtime-rca-worker",
            daemon=True,
        )

        self.thread.start()

    def submit(self, payload):
        with self.condition:
            if not self.accepting:
                return False

            try:
                self.queue.put_nowait(payload)
                self.pending += 1
                return True

            except queue.Full:
                logger.warning("Runtime RCA queue is full. Dropping event.")
                return False

    def _run(self):
        while True:
            payload = self.queue.get()

            try:
                if payload is None:
                    return

                try:
                    self.transport.send_event(payload)

                except Exception:
                    logger.exception(
                        "Runtime RCA background delivery failed."
                    )

            finally:
                if payload is not None:
                    with self.condition:
                        self.pending -= 1
                        self.condition.notify_all()

                self.queue.task_done()

    def flush(self, timeout=None):
        deadline = (
            None if timeout is None
            else time.monotonic() + timeout
        )

        with self.condition:
            while self.pending > 0:
                if deadline is None:
                    self.condition.wait()
                    continue

                remaining = deadline - time.monotonic()

                if remaining <= 0:
                    return False

                self.condition.wait(remaining)

        return True

    def close(self, timeout=5):
        with self.condition:
            self.accepting = False

        flushed = self.flush(timeout=timeout)

        if not self.thread.is_alive():
            return flushed

        try:
            self.queue.put(None, timeout=max(timeout, 0))
        except queue.Full:
            logger.warning("Could not enqueue worker shutdown signal.")
            return False

        self.thread.join(timeout=max(timeout, 0))

        return flushed and not self.thread.is_alive()