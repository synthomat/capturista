import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass

from playwright.sync_api import sync_playwright


@dataclass(frozen=True)
class Slot:
    key: str
    value: str


class AbstractLoader(ABC):
    # names of optional parameters
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
    def handle(self, context):
        raise NotImplementedError()

    def set_config(self, config):
        self.config = config


class PlaywrightLoader(AbstractLoader):
    def __init__(self, manager, task):
        super().__init__(manager, task)

    def run(self):
        with sync_playwright() as playwright:
            chromium = playwright.chromium  # or "firefox" or "webkit".
            self.manager.update_status_for(self.task, "launching browser")
            browser = chromium.launch()

            context = browser.new_context(
                viewport={'width': 2560, 'height': 1440},
                device_scale_factor=2
            )

            self.update_status("running handler logic")
            self.handle(context)

            self.update_status("closing browser")
            browser.close()
            self.update_status("done")

    @abstractmethod
    def handle(self, context):
        raise NotImplementedError()
