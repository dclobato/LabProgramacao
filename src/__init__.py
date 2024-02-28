import json
import logging
import os
import random
import shutil
import uuid
from pathlib import Path

from flask import Flask, render_template
from flask_migrate import init, upgrade, revision
from sqlalchemy import select

from src.models.auth import User
from src.models.categoria import Categoria
from src.models.produto import Produto
from src.modules import bootstrap, minify, db, migration, csrf, login, mail
from src.routes import auth
from src.utils import as_localtime


def create_app(config_filename: str = "config.dev.json") -> Flask:
    app = Flask(__name__,
                instance_relative_config=True,
                static_folder='static',
                template_folder='templates')

    # Desativar as mensagens do servidor HTTP
    # https://stackoverflow.com/a/18379764
    # logging.getLogger('werkzeug').setLevel(logging.ERROR)

    if not Path(app.instance_path).is_dir():
        try:
            os.makedirs(app.instance_path)
        except OSError:
            pass

    # Definindo o nível de logging da aplicação
    app.logger.setLevel(logging.DEBUG)

    app.logger.debug(f"Carregando o arquivo de configuração {config_filename}")
    try:
        app.config.from_file(config_filename, load=json.load)
    except FileNotFoundError as e:
        app.logger.fatal(f"Arquivo '{config_filename}' não encontrado")
        app.logger.fatal(f"Exception: {e}")
        exit(1)

    app.logger.debug("Inicializando módulos básicos")
    bootstrap.init_app(app)
    if app.config["MINIFY"]:
        minify.init_app(app)
    db.init_app(app)
    migration.init_app(app,
                       db,
                       directory=app.config.get("MIGRATION_DIR", "src/migrations"),
                       render_as_batch=False)
    csrf.init_app(app)
    login.init_app(app)
    mail.init_app(app)

    # Formatando as datas para horário local
    # https://stackoverflow.com/q/65359968
    app.jinja_env.filters["as_localtime"] = as_localtime

    @login.user_loader
    def load_user(user_id):
        try:
            auth_id = uuid.UUID(str(user_id))
        except ValueError:
            return None
        else:
            # noinspection PyTestUnpassedFixture
            return db.session.execute(db.select(User).where(User.id == auth_id).limit(1)).scalar()

    with app.app_context():
        # Se estivéssemos usando um SGBD, poderíamos consultar os metadados
        # do esquema com algo como a linha abaixo para o MariaDB/MySQL
        # SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'DBName'
        # Como o sqlite é um arquivo no sistema de arquivos, vamos simplesmente
        # verificar se o arquivo existe
        arquivo = Path(app.instance_path) / Path(app.config["SQLITE_DB_NAME"])
        if not arquivo.is_file():
            app.logger.info(f"Criando o banco de dados em {arquivo}")
            if Path(migration.directory).is_dir():
                app.logger.info(f"Removendo o diretorio anterior de migracoes")
                shutil.rmtree(Path(migration.directory))
            app.logger.info(f"Efetuando a migração inicial")
            init()
            revision(message="Migracao inicial de dentro da App",
                     autogenerate=True,
                     head="head")
            upgrade(revision="head")

            if db.session.execute(select(Categoria.id).limit(1)).scalar_one_or_none() is None:
                from src.models.seed import seed_data
                app.logger.info("Semeando as tabelas")
                for seed in seed_data:
                    categoria = Categoria()
                    categoria.nome = seed["categoria"]
                    db.session.add(categoria)
                    for p in seed["produtos"]:
                        produto = Produto()
                        produto.nome = p["nome"]
                        produto.preco = p["preco"]
                        produto.estoque = random.randrange(-5, 60)
                        produto.ativo = random.random() < 0.8
                        produto.categoria = categoria
                        db.session.add(produto)
                    db.session.commit()
                app.logger.info("Semeadura das tabelas concluída")

        if db.session.execute(select(User.id).limit(1)).scalar_one_or_none() is None:
            app.logger.info("Adicionando usuário inicial")
            usuario = User()
            usuario.nome = "Administrador"
            usuario.email = "admin@admin.com.br"
            usuario.set_password("123")
            usuario.email_validado = True
            usuario.usa_2fa = False
            app.logger.info(f"Ususario '{usuario.email}', senha '123'")
            db.session.add(usuario)
            db.session.commit()

    app.logger.debug("Registrando as blueprints")
    app.register_blueprint(auth.bp)

    @app.route("/")
    @app.route("/index")
    def index():
        return render_template("index.jinja", title="Página inicial")

    return app
