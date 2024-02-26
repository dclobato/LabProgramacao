from flask_bootstrap import Bootstrap5
from flask_migrate import Migrate
from flask_minify import Minify
from flask_sqlalchemy import SQLAlchemy

from src.models import Base

minify = Minify()
bootstrap = Bootstrap5()
db = SQLAlchemy(model_class=Base,
                disable_autonaming=True)
migration = Migrate(render_as_batch=True)
