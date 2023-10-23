from playwright.sync_api import BrowserContext

from capturista.loaders.loader import PlaywrightLoader, ParamSlot


class WebLoader(PlaywrightLoader):
    uid = "6d0115ae-765b-4cbb-b387-02a0391a732b"
    name = "web"

    param_slots = PlaywrightLoader.param_slots.extend(
        ParamSlot(key="auth_header")
    )

    def handle(self, context: BrowserContext):
        page = context.new_page()
        self.update_status("navigating to URL")
        page.goto(self.task.params['url'])
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(3000)

        self.update_status("capturing screen")
        buffer = page.screenshot()
        self.manager.on_capture_result(self.task, buffer)
