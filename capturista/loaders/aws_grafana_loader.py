import logging
import sys

from capturista.loaders.loader import PlaywrightLoader
from playwright.sync_api import sync_playwright


class AWSGrafanaLoader(PlaywrightLoader):
    input_slots = [
        "api_token",
        "screen_width",
        "screen_height"
    ]

    def handle(self, context): pass

    def run(self):
        with sync_playwright() as playwright:
            params = self.task.params
            slot_params = self.task.slot_params

            chromium = playwright.chromium  # or "firefox" or "webkit".
            browser = chromium.launch()

            context = browser.new_context(
                viewport={'width': int(slot_params.get('screen_width')), 'height': int(slot_params.get('screen_height'))},
                device_scale_factor=2
            )

            page = context.new_page()
            self.update_status("navigating to URL")
            page.set_extra_http_headers(headers={"Authorization": "Bearer " + slot_params.get('api_token')})
            page.goto(params.get('url'))
            page.wait_for_load_state('networkidle')

            # after successful login we wait again for the page to build up fully
            self.update_status("logged in successfully")

            self.update_status("capturing screen")
            buffer = page.screenshot()

            self.manager.on_capture_result(self.task, buffer)
            self.update_status("running handler logic")
            # self.handle(context)

            self.update_status("closing browser")
            browser.close()
            self.update_status("done")
