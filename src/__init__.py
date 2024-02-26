import json
import logging
import os
import shutil
from pathlib import Path

from flask import Flask, render_template
from flask_migrate import init, upgrade, revision

from src.modules import bootstrap, minify, db, migration


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

    @app.route("/")
    @app.route("/index")
    def index():
        return render_template("index.jinja", title="Página inicial")

    return app
