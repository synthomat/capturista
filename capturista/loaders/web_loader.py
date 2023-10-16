from capturista.loaders.loader import PlaywrightLoader


class WebLoader(PlaywrightLoader):
    uid = "6d0115ae-765b-4cbb-b387-02a0391a732b"

    def handle(self, context):
        page = context.new_page()
        self.update_status("navigating to URL")
        page.goto(self.task.params['url'])
        page.wait_for_load_state('networkidle')

        page.wait_for_timeout(3000)

        self.update_status("capturing screen")
        buffer = page.screenshot()
        self.manager.on_capture_result(self.task, buffer)
