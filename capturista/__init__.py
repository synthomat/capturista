import logging
import os
import threading
import time
import uuid
from datetime import datetime
from queue import Queue

from PIL import Image
from flask import Flask, request, render_template, redirect, make_response
from tinydb import TinyDB, Query

from capturista.loaders.kibana_loader import KibanaLoader
from capturista.loaders.tableau_loader import TableauLoader
from capturista.loaders.web_loader import WebLoader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger("werkzeug").setLevel(logging.WARN)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

db = TinyDB('db.json')

TASK_QUEUE = Queue()
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, validators, URLField, SelectField


class CreateSourceForm(FlaskForm):
    name = StringField('Name', [validators.Length(min=3)])
    target_url = URLField('Target URL', [validators.Length(min=10)])
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
            img.thumbnail((300, 300))
            img.save(f"capturista/static/screencaptures/{task.config_id}.thumb.png")

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
    "tableau": TableauLoader
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

            time.sleep(60 * 10)

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

    @app.get("/api/capture_types/slots")
    def capture_slots():
        typ = request.args.get('capture_type')
        cls = LOADER_TYPES.get(typ)
        slots = cls.input_slots

        return render_template("slots.html", slots=slots)

    def dynamic_slots(form):
        slot_fields = filter(lambda k: k.startswith('slot_'), form.keys())

        slot_params = {}

        for slot_name in slot_fields:
            _, _, name = slot_name.partition('_')
            slot_params[name] = form[slot_name]

        return slot_params

    @app.route("/sources/<id>/edit", methods=["get", "post"])
    def cs_edit(id):
        capture_configs = db.table('capture_configs')
        cs = capture_configs.get(Query().id == id)

        types = sorted(LOADER_TYPES.keys())

        if request.method == "POST":
            f = request.form

            new = dict(
                name=f.get('name'),
                params=dict(
                    url=f.get('url')
                ),
                autoload=f.get('autoload') is not None,
                capture_type=f.get('capture_type'),
                slot_params=dynamic_slots(f)
            )

            capture_configs.update(new, Query().id == id)
            return redirect("/")

        cls = LOADER_TYPES.get(cs.get('capture_type'))
        slots = cls.input_slots
        return render_template("cs-edit.html", cs=cs, capture_types=types, slots=slots)

    @app.delete("/api/sources/<id>")
    def cs_delete(id):
        capture_configs = db.table('capture_configs')
        capture_configs.remove(Query().id == id)

        response = make_response({}, 204)

        response.headers['HX-Redirect'] = '/'

        return response

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
