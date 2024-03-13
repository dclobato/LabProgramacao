from flask_bootstrap import Bootstrap5
from flask_login import LoginManager
from flask_mailman import Mail
from flask_migrate import Migrate
from flask_minify import Minify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    # Se houver atributo comum a todas as classes, pode adicionar aqui,
    # que serão incluidas nas classes filhas, e como atributos no BD
    pass


minify = Minify()
bootstrap = Bootstrap5()
db = SQLAlchemy(model_class=Base, disable_autonaming=True)
migration = Migrate(render_as_batch=True)
csrf = CSRFProtect()
login = LoginManager()
mail = Mail()
