import json
import logging
import os

from flask import Flask, render_template

from modules import bootstrap, minify


def create_app(config_filename: str = "config.dev.json") -> Flask:
    app = Flask(__name__,
                instance_relative_config=True,
                static_folder='static',
                template_folder='templates')

    # Desativar as mensagens do servidor HTTP
    # https://stackoverflow.com/a/18379764
    # logging.getLogger('werkzeug').setLevel(logging.ERROR)

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

    @app.route("/")
    @app.route("/index")
    def index():
        return render_template("index.jinja", title="Página inicial")

    return app
