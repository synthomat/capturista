import logging
import sys

from playwright.sync_api import sync_playwright

from loaders.loader import AbstractLoader


class TableauLoader(AbstractLoader):
    input_slots = [
        "username",
        "password"
    ]

    def run(self, playwright):
        params = self.task.params
        slot_params = self.task.slot_params
        chromium = playwright.chromium  # or "firefox" or "webkit".
        self.update_status("opening browser")
        browser = chromium.launch()

        context = browser.new_context(
            viewport={'width': 2560, 'height': 1440},
            device_scale_factor=2
        )

        page = context.new_page()
        self.update_status("navigating to URL")
        page.goto(params.get('url'))
        page.wait_for_load_state('networkidle')

        self.update_status("logging in")

        page.locator('input[name="email"]').fill(slot_params.get('username'))
        page.click('button[id="login-submit"]')
        page.locator('input[name="password"]').fill(slot_params.get('password'))
        page.click('button[id="login-submit"]')

        # wait for page reaction
        page.wait_for_timeout(3000)

        # after successful login we wait again for the page to build up fully
        page.wait_for_timeout(6000)
        self.update_status("logged in successfully")

        self.update_status("taking screen capture")
        original_path = f"static/screencaptures/{self.task.config_id}.png"
        buffer = page.screenshot()
        self.manager.on_capture_result(self.task, buffer)
        # other actions...
        browser.close()
        """
        image = Image.frombuffer(buffer)

        d1 = ImageDraw.Draw(image)
        font = ImageFont.truetype("Montserrat-Regular.ttf", 60)
        d1.text((800, 20), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), fill=(50, 50, 50), font=font)
        image.save(original_path)

        MAX_SIZE = (400, 400)
        
        image.thumbnail(MAX_SIZE)
        
        # creating thumbnail
        image.save('static/screencaptures/b83d13d1-cf0a-4277-83bf-1e9ff16e5fa6.thumb.png')
        """
        self.update_status("done capturing screen")

        print("Done screencapture")

    def handle(self):
        with sync_playwright() as playwright:
            self.run(playwright)
