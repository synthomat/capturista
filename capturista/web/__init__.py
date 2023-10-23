import json
import logging
import os
import uuid
from queue import Queue

from flask import Flask, render_template, redirect, make_response
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, FormField

from capturista.loaders.kibana_loader import KibanaLoader
from capturista.loaders.loader import LoaderRegistry
from capturista.loaders.web_loader import WebLoader
from capturista.web.forms import CreateSourceForm, SlotForm, BaseSourceForm, EditSourceForm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger("werkzeug").setLevel(logging.WARN)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

TASK_QUEUE = Queue()

from capturista.core.models import db as dba, DataSourceRepository, DataSource


class CaptureSource:
    def __init__(self, _id, name) -> None:
        self.id = _id
        self.name = name
        self.url = None
        self.loader_type = None


from flask_migrate import Migrate

from flask_wtf import FlaskForm


def create_app() -> Flask:
    loader_registry = LoaderRegistry()
    loader_registry.register([
        WebLoader,
        KibanaLoader
    ])

    app = Flask(__name__)
    app.config['SECRET_KEY'] = str(uuid.uuid4())  # this should actually be a configurable static value
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///capturista.sqlite"

    dba.init_app(app)
    migrate = Migrate(app, dba)

    csrf = CSRFProtect()
    csrf.init_app(app)

    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        # Scheduler().start()
        # Consumer().start()
        pass

    data_source_repo = DataSourceRepository(dba.session)

    @app.route("/")
    def overview():
        sources = data_source_repo.get_all()
        ll = loader_registry.get_loader_names()

        loader_names = {k: v for k, v in ll}

        return render_template("index.html",
                               sources=sources,
                               loader_names=loader_names)

    @app.route("/api/sources/<sid>/trigger", methods=["PUT"])
    def trigger_run(sid: str):
        return {"status": "enqueued"}

    @app.route("/sources/new", methods=["get", "post"])
    def cs_new():
        loaders = loader_registry.get_loader_names()

        form = CreateSourceForm()
        form.loader_id.choices = [(l[0], l[1].capitalize()) for l in loaders]

        if form.validate_on_submit():
            ds = DataSource()
            form.populate_obj(ds)

            dba.session.add(ds)
            dba.session.commit()

            return redirect("/")

        return render_template("cs-new.html", form=form)

    @app.route("/sources/<sid>/edit", methods=["get", "post"])
    def cs_edit(sid: str):
        data_source = data_source_repo.get_by_id(sid)
        loader_cls = loader_registry.get_by_id(str(data_source.loader_id))

        class Slots(FlaskForm):
            def populate_obj(self, obj):
                data = self.data.copy()
                del data['csrf_token']

                obj.custom_config = data

        for slot in loader_cls.param_slots.slots:
            setattr(Slots, slot.key, StringField(default=slot.default))

        form = EditSourceForm(obj=data_source)

        slots_form = Slots(data=data_source.custom_config, prefix="p-")

        if form.validate_on_submit() and slots_form.validate_on_submit():

            form.populate_obj(data_source)
            slots_form.populate_obj(data_source)
            dba.session.commit()

            return redirect("/")

        return render_template("cs-edit.html",
                               cs=data_source,
                               form=form,
                               slots_form=slots_form)

    @app.delete("/api/sources/<sid>")
    def cs_delete(sid: str):
        ds = data_source_repo.get_by_id(sid)

        success = data_source_repo.delete_by_id(sid)

        response = make_response({}, 204)
        response.headers['HX-Redirect'] = '/'

        return response

    return app
