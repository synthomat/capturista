import threading
from abc import ABC, abstractmethod


class AbstractLoader(ABC):
    input_slots = []

    def __init__(self, manager, task):
        super().__init__()
        self.manager = manager
        self.task = task
        self._stop_event = threading.Event()
        self.config = {}

    def stop(self) -> None:
        self._stop_event.set()

    def _stopped(self) -> bool:
        return self._stop_event.is_set()

    def update_status(self, status: str):
        self.manager.update_status_for(self.task, status)

    @abstractmethod
    def handle(self):
        raise NotImplementedError()

    def set_config(self, config):
        self.config = config
