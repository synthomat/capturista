from capturista.loaders.loader import PlaywrightLoader


class TableauLoader(PlaywrightLoader):
    input_slots = [
        "username",
        "password"
    ]

    def step_close_popup(self, page):
        self.update_status("waiting for a popup")

        try:
            page.click('button[data-tb-test-id="postlogin-footer-close-Button"]', timeout=5000)
            self.update_status("closed popup successfully")
        except:
            self.update_status("no popup appeared")

    def handle(self, context):
        params = self.task.params
        slot_params = self.task.slot_params

        page = context.new_page()
        self.update_status("navigating to URL")

        page.goto(params.get('url'))
        page.wait_for_load_state('networkidle')

        self.update_status("logging in")

        page.locator('input[name="email"]').fill(slot_params.get('username'))
        page.click('button[id="login-submit"]')
        page.locator('input[name="password"]').fill(slot_params.get('password'))
        page.click('button[id="login-submit"]')

        try:
            self.update_status("waiting for network to calm down")
            page.wait_for_load_state('networkidle', timeout=8000)
        except:
            self.update_status("network doesn't calm down – trying to continue")

        self.update_status("logged in successfully")

        self.step_close_popup(page)
        page.wait_for_timeout(1000)
        frame_url = page.main_frame.child_frames[0].url
        page.goto(frame_url)

        page.wait_for_timeout(2000)
        self.update_status("capturing screen")
        buffer = page.screenshot()
        self.manager.on_capture_result(self.task, buffer)


