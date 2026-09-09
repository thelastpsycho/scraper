import queue
import threading

# Create a queue to store log messages
log_queue = queue.Queue()


class RunControl:
    """Cooperative stop/pause signaling for the background allotment-update
    thread. Checked once per batch iteration in update_pms_cm_allotment.py
    and update_rest_allotment.py."""

    def __init__(self):
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()

    def reset(self):
        self.stop_event.clear()
        self.pause_event.clear()


allotment_run_control = RunControl()
