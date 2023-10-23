import uuid

from wtforms import StringField, validators, URLField, SelectField, FormField, BooleanField, IntegerField, TextAreaField
from flask_wtf import FlaskForm


class SlotForm(FlaskForm):
    pass


class BaseSourceForm(FlaskForm):
    class ScreenResolution(FlaskForm):
        width = IntegerField('Width (px)', default=2560)
        height = IntegerField('Height (px)', default=1440)

    is_active = BooleanField('Enabled', default=True)
    name = StringField('Name', [validators.Length(min=3)])
    target_url = URLField('Target URL', [validators.Length(min=10)])
    # resolution = FormField(ScreenResolution)


class EditSourceForm(BaseSourceForm):
    #custom_config = TextAreaField(render_kw={'rows': 10})
    pass


class CreateSourceForm(BaseSourceForm):
    loader_id = SelectField('Loader Type', choices=[], coerce=uuid.UUID)
    #defaults = BooleanField('Apply default config', default=True)
