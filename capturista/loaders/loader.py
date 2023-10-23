import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Type

from playwright.sync_api import sync_playwright, BrowserContext


class Config:
    def __init__(self, init=None):
        if init is None:
            init = {}
        self.vals = init

    def extend(self, vals: dict):
        self.vals.update(vals)

        return self

    def __call__(self, vals):
        return self.extend(vals)

    def copy(self):
        return self.vals.copy()

    def __getitem__(self, item):
        return self.vals[item]


@dataclass
class ParamSlot:
    key: str
    default: str = None
    is_secret: bool = False


class ParamSlots:
    def __init__(self, *slots):
        self.slots = slots

    def extend(self, *slots):
        self.slots += slots
        return self

class AbstractLoader(ABC):
    """You should not use this class directly"""
    default_config = Config(dict(blik=False))
    # names of optional parameters
    uid = None
    name = None

    param_slots = ParamSlots()

    config = {}

    def __init__(self, manager, task):
        super().__init__()
        self.manager = manager
        self.task = task
        self._stop_event = threading.Event()

        # populated from database
        self.custom_config = {}

        self.runtime_config = {}
        self.reset_config()

    def stop(self) -> None:
        self._stop_event.set()

    def _stopped(self) -> bool:
        return self._stop_event.is_set()

    def update_status(self, status: str):
        self.manager.update_status_for(self.task, status)

    def apply_config(self, config):
        self.runtime_config.update(config)

    def reset_config(self):
        self.runtime_config = self.default_config.copy()

    @abstractmethod
    def handle(self, context):
        raise NotImplementedError()



class PlaywrightLoader(AbstractLoader):
    """Default implementation for browser based loaders"""
    param_slots = AbstractLoader.param_slots.extend(
        ParamSlot(key="width_height_scale", default="2560,1440,2"),
        ParamSlot(key="secret", is_secret=True)
    )

    def __init__(self, manager=None, task=None):
        super().__init__(manager, task)

    def run(self):
        with sync_playwright() as playwright:
            chromium = playwright.chromium  # or "firefox" or "webkit".
            self.manager.update_status_for(self.task, "launching browser")

            browser = chromium.launch()

            screen = self.default_config['screen']
            width, height = screen['width'], screen['height']
            scale = screen['scale']

            context = browser.new_context(
                viewport={'width': width, 'height': height},
                device_scale_factor=scale
            )
            self.update_status("running handler logic")
            self.handle(context)

            self.update_status("closing browser")
            browser.close()
            self.update_status("done")

    def create_context(self):
        pass

    @abstractmethod
    def handle(self, context: BrowserContext):
        raise NotImplementedError()


class LoaderRegistry:
    def __init__(self):
        self.loaders: dict[str, type[AbstractLoader]] = {}

    def register(self, loader: type[AbstractLoader] | list[type[AbstractLoader]]):
        loaders = loader if type(loader) is list else [loader]

        for loader in loaders:
            self.loaders[loader.uid] = loader

    def get_by_id(self, lid) -> type[AbstractLoader]:
        return self.loaders[lid]

    def get_loader_names(self) -> list[tuple[str, str]]:
        names = []
        for uid, ldr in self.loaders.items():
            names.append((uid, ldr.name))

        return names
