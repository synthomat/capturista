import logging
import os
import threading
import time
import uuid
from datetime import datetime
from queue import Queue

from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, redirect, make_response
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from tinydb import TinyDB, Query
from wtforms import StringField, validators, URLField, SelectField, FormField, BooleanField

from capturista.loaders.kibana_loader import KibanaLoader
from capturista.loaders.tableau_loader import TableauLoader
from capturista.loaders.web_loader import WebLoader
from capturista.loaders.aws_grafana_loader import AWSGrafanaLoader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger("werkzeug").setLevel(logging.WARN)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

db = TinyDB('db.json')

TASK_QUEUE = Queue()


class BaseSourceForm(FlaskForm):
    name = StringField('Name', [validators.Length(min=3)])
    target_url = URLField('Target URL', [validators.Length(min=10)])
    autoload = BooleanField('Auto Load', default=True)


class CreateSourceForm(BaseSourceForm):
    loader_type = SelectField('Loader Type', choices=[])

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

        logger.info(f"{task.config_id}: {status}")

    def on_capture_result(self, task: CaptureTask, buffer):
        img_path = f"capturista/static/screencaptures/{task.config_id}.png"
        with open(img_path, 'wb') as f:
            f.write(buffer)

        with Image.open(img_path) as img:
            d = ImageDraw.Draw(img)
            text = datetime.now().strftime("%Y-%m-%d %H:%M")
            font = ImageFont.truetype("capturista/web/static/fonts/SourceSans3-Regular.ttf", 40)
            text_x, text_y = (2560*2)-380, 50
            text_width, text_height = font.getmask(text).size
            d.rectangle(((text_x-15, text_y-5), (text_x + text_width+15, text_y + text_height+30)), fill=(230, 100, 100, 100))
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


class CaptureSource:
    def __init__(self, _id, name) -> None:
        self.id = _id
        self.name = name
        self.url = None
        self.loader_type = None


manager = Manager()

LOADER_TYPES = {
    "web": WebLoader,
    "kibana": KibanaLoader,
    "tableau": TableauLoader,
    "aws_grafana":AWSGrafanaLoader
}


class Scheduler(threading.Thread):
    """"""

    def __init__(self):
        super().__init__(daemon=True)

    def run(self):
        logging.info("Task Scheduler started")
        capture_configs = db.table('capture_configs')

        while True:
            sources = capture_configs.search(Query().autoload == True)

            for config in sources:
                task = CaptureTask(
                    config['id'],
                    config['capture_type'],
                    params=config.get('params'),
                    slot_params=config.get('slot_params')
                )

                TASK_QUEUE.put(task)

            time.sleep(60 * 30)

        logging.info("Task Scheduler stopped")


class Consumer(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self._stop_event = threading.Event()

    def run(self):
        logging.info("Task Consumer started")

        while not self._stop_event.is_set():
            task = TASK_QUEUE.get()
            capture_type = task.capture_type
            # LOADERS[_id]["status"] = "started"
            loader_cls = LOADER_TYPES.get(capture_type, None)

            if not loader_cls:
                continue

            try:
                loader = loader_cls(manager, task)
                loader.run()
            except Exception as e:
                logging.error(e)

        logging.info("Task Consumer stopped")


csrf = CSRFProtect()


def dynamic_slots(form):
    slot_fields = filter(lambda k: k.startswith('slot_'), form.keys())

    slot_params = {}

    for slot_name in slot_fields:
        _, _, name = slot_name.partition('_')
        slot_params[name] = form[slot_name]

    return slot_params


def create_app() -> Flask:
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "6592f711-2247-454a"

    csrf.init_app(app)
    # app.config.from_pyfile(config_filename)

    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        Scheduler().start()
        Consumer().start()

    @app.route("/")
    def overview():
        capture_configs = db.table('capture_configs')
        return render_template("index.html", capture_configs=capture_configs)

    @app.route("/api/sources/<id>/trigger", methods=["PUT"])
    def trigger_source(id):
        capture_configs = db.table('capture_configs')
        config = capture_configs.get(Query().id == id)

        task = CaptureTask(
            id,
            config['capture_type'],
            params=config.get('params'),
            slot_params=config.get('slot_params')
        )

        TASK_QUEUE.put(task)

        return {"status": "enqueued"}

    @app.get("/api/states")
    def all_states():
        capture_configs = db.table('capture_configs')
        all = capture_configs.all()

        for a in all:
            del a['params']
            a['thumbnail_url'] = f"/static/screencaptures/{a.get('id')}.thumb.png",
            a['image_url'] = f"/static/screencaptures/{a.get('id')}.png"

        state = dict(
            instances=all,
            queue_length=TASK_QUEUE.qsize()
        )

        return state

    @app.get("/api/capture_types")
    def capture_types():
        types = sorted(LOADER_TYPES.keys())

        return types

    @app.route("/sources/new", methods=["get", "post"])
    def cs_new():
        types = sorted(LOADER_TYPES.keys())

        form = CreateSourceForm()
        form.loader_type.choices = [(t, t.capitalize()) for t in types]

        if form.validate_on_submit():
            new = dict(
                id=str(uuid.uuid4()),
                name=form.name.data,
                params=dict(
                    url=form.target_url.data
                ),
                capture_type=form.loader_type.data
            )
            capture_configs = db.table('capture_configs')
            capture_configs.insert(new)

            return redirect("/")

        return render_template("cs-new.html", form=form)

    @app.route("/sources/<id>/edit", methods=["get", "post"])
    def cs_edit(id):
        capture_configs = db.table('capture_configs')
        cs = capture_configs.get(Query().id == id)

        class SlotForm(FlaskForm):
            pass

        t = LOADER_TYPES.get(cs.get("capture_type"))

        for slot in t.input_slots:
            setattr(SlotForm, slot, StringField())

#        setattr(SlotForm, slot, StringField())

        class F(BaseSourceForm):
            slots = FormField(SlotForm)

        slot_params = cs.get('slot_params', {}).copy()

        if 'password' in slot_params:
            slot_params['password'] = '****'

        if 'api_token' in slot_params:
            slot_params['api_token'] = '****'

        form = F(data=dict(
            name=cs.get('name'),
            autoload=cs.get('autoload'),
            target_url=cs.get('params').get('url'),
            slots=slot_params))

        if form.validate_on_submit():
            f = form.data
            slot_data = form.slots.data
            del slot_data['csrf_token']

            if 'password' in slot_data:
                if slot_data['password'].strip() in ['', '****']:
                    # recover original password
                    slot_data['password'] = cs.get('slot_params').get('password')

                if slot_data['api_token'].strip() in ['', '****']:
                    # recover original api_token
                    slot_data['api_token'] = cs.get('slot_params').get('api_token')

            new = dict(
                name=f.get('name'),
                params=dict(
                    url=f.get('target_url')
                ),
                autoload=f.get('autoload'),
                capture_type=cs.get('capture_type'),
                slot_params=slot_data
            )

            capture_configs.update(new, Query().id == id)
            return redirect("/")

        return render_template("cs-edit.html", cs=cs, form=form)

    @app.delete("/api/sources/<id>")
    def cs_delete(id):
        capture_configs = db.table('capture_configs')
        capture_configs.remove(Query().id == id)

        response = make_response({}, 204)

        response.headers['HX-Redirect'] = '/'

        return response

    return app


def main():
    capture_configs = db.table('capture_configs')
    print(capture_configs.all())

    app = create_app()
    app.run(
        host=os.getenv("BIND", "0.0.0.0"),
        port=os.getenv('PORT', 5000)
    )


if __name__ == '__main__':
    main()
