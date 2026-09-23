import queue
import threading

# Create a queue to store log messages
log_queue = queue.Queue()


class RunControl:
    """Cooperative stop/pause signaling for the background allotment-update
    thread. Checked once per batch iteration in integrations/pms/allotment_updater.py
    and integrations/pms/other_room_allotment_updater.py."""

    def __init__(self):
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()

    def reset(self):
        self.stop_event.clear()
        self.pause_event.clear()


allotment_run_control = RunControl()
