import logging
import sys

from loaders.loader import PlaywrightLoader


class KibanaLoader(PlaywrightLoader):
    input_slots = [
        "username",
        "password"
    ]

    def handle(self, context):
        params = self.task.params
        slot_params = self.task.slot_params

        page = context.new_page()
        self.update_status("navigating to URL")
        page.goto(params.get('url'))
        page.wait_for_load_state('networkidle')

        self.update_status("logging in")
        page.locator('input[name="username"]').fill(slot_params.get('username'))
        page.locator('input[name="password"]').fill(slot_params.get('password'))
        page.click('button[type="submit"]')

        # wait for page reaction
        page.wait_for_timeout(3000)

        login_error = page.locator('div[data-test-subj="loginErrorMessage"]')

        if login_error.count() > 0:
            logging.error("Could not log into the dashboard. Aborting.")
            # browser.close()
            sys.exit(1)

        # after successful login we wait again for the page to build up fully
        page.wait_for_timeout(6000)
        self.update_status("logged in successfully")

        page.click('button[data-test-subj="dashboardFullScreenMode"]')
        page.click('button[data-test-subj="toastCloseButton"]')
        page.wait_for_timeout(2000)

        self.update_status("capturing screen")
        buffer = page.screenshot()

        self.manager.on_capture_result(self.task, buffer)
