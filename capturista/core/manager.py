from datetime import datetime
from PIL import ImageFont, ImageDraw, Image

class CaptureTask:
    def __init__(self, config_id, capture_type: str, params=None, slot_params=None):
        self.config_id = config_id
        self.capture_type = capture_type
        self.params = params
        self.slot_params = slot_params or {}

class Manager:
    def __init__(self):
        self.messages = []

    def update_status_for(self, task: CaptureTask, status):
        capture_configs = db.table('capture_configs')
        capture_configs.update(dict(status=status), Query().id == task.config_id)

        #logger.info(f"{task.config_id}: {status}")

    def on_capture_result(self, task: CaptureTask, buffer):
        img_path = f"capturista/static/screencaptures/{task.config_id}.png"
        with open(img_path, 'wb') as f:
            f.write(buffer)

        with Image.open(img_path) as img:
            d = ImageDraw.Draw(img)
            text = datetime.now().strftime("%Y-%m-%d %H:%M")
            font = ImageFont.truetype("capturista/web/static/fonts/SourceSans3-Regular.ttf", 40)
            text_x, text_y = (2560 * 2) - 380, 50
            text_width, text_height = font.getmask(text).size
            d.rectangle(((text_x - 15, text_y - 5), (text_x + text_width + 15, text_y + text_height + 30)),
                        fill=(230, 100, 100, 100))
            d.text((text_x, text_y), text, font=font, fill=(70, 30, 30))

            img.save(img_path)

            img.thumbnail((300, 300))
            img.save(f"capturista/web/static/screencaptures/{task.config_id}.thumb.png")

        capture_configs = db.table('capture_configs')
        capture_configs.update(dict(last_run=datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                               Query().id == task.config_id)

    def on_fail(self, task: CaptureTask, reason):
        pass

    def on_done(self, task: CaptureTask):
        pass
