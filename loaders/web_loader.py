import logging
import sys

from playwright.sync_api import sync_playwright
from .loader import AbstractLoader
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime


class WebLoader(AbstractLoader):
    uid = "6d0115ae-765b-4cbb-b387-02a0391a732b"

    def run(self, playwright):
        chromium = playwright.chromium  # or "firefox" or "webkit".
        self.update_status("opening browser")
        browser = chromium.launch()

        context = browser.new_context(
            viewport={'width': 2560, 'height': 1440},
            device_scale_factor=2
        )

        page = context.new_page()
        self.update_status("navigating to URL")
        page.goto(self.task.params['url'])
        page.wait_for_load_state('networkidle')

        page.wait_for_timeout(3000)

        self.update_status("taking screen capture")
        buffer = page.screenshot()
        self.manager.on_capture_result(self.task, buffer)

        # other actions...
        browser.close()

        self.update_status("done capturing screen")

    def handle(self):
        with sync_playwright() as playwright:
            self.run(playwright)
