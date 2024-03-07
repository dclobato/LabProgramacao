import json
import logging
import os
import random
import shutil
import uuid
from pathlib import Path

import email_validator
from flask import Flask, render_template
from flask_migrate import init, upgrade, revision
from sqlalchemy import select

import src.routes.auth
import src.routes.categoria
import src.routes.produto
from src.models.auth import User
from src.models.categoria import Categoria
from src.models.produto import Produto
from src.modules import bootstrap, minify, db, migration, csrf, login, mail
from src.utils import as_localtime, normalized_email


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

    if app.config.get("SECRET_KEY", None) is None:
        app.logger.fatal(f"Necessário definir a SECRET_KEY da aplicação no arquivo {config_filename}")
        exit(1)

    app.logger.debug("Inicializando módulos básicos")
    bootstrap.init_app(app)
    if app.config.get("MINIFY", True):
        minify.init_app(app)
    db.init_app(app)
    migration.init_app(app,
                       db,
                       directory=app.config.get("MIGRATION_DIR", "src/migrations"),
                       render_as_batch=False)
    csrf.init_app(app)
    mail.init_app(app)
    login.init_app(app)
    login.login_view = "auth.login"
    login.login_message = "É necessário estar logado para acessar esta funcionalidade"
    login.login_message_category = "warning"
    login.session_protection = "strong"
    email_validator.CHECK_DELIVERABILITY = False

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
            return db.session.execute(db.select(User).where(User.id == auth_id).limit(1)).scalar_one_or_none()

    app.logger.debug("Registrando as blueprints")
    app.register_blueprint(src.routes.auth.bp)
    app.register_blueprint(src.routes.categoria.bp)
    app.register_blueprint(src.routes.produto.bp)

    with app.app_context():
        # Se estivéssemos usando um SGBD, poderíamos consultar os metadados
        # do esquema com algo como a linha abaixo para o MariaDB/MySQL
        # SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'DBName'
        # Como o sqlite é um arquivo no sistema de arquivos, vamos simplesmente
        # verificar se o arquivo existe
        arquivo = Path(app.instance_path) / Path(app.config.get("SQLITE_DB_NAME", "application_db.sqlite3"))
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
            email = "admin@admin.com.br"
            senha = "123"
            app.logger.info(f"Adicionando usuário inicial ({email}:{senha})")
            usuario = User()
            usuario.nome = "Administrador"
            usuario.email = normalized_email(email)
            usuario.set_password(senha)
            usuario.email_validado = True
            usuario.usa_2fa = False
            app.logger.info(f"Ususario '{usuario.email}', senha '123'")
            db.session.add(usuario)
            db.session.commit()

        if db.session.execute(select(Categoria.id).limit(1)).scalar_one_or_none() is None:
            from src.models.seed import seed_data
            app.logger.info("Semeando as tabelas")
            cc = pc = 0
            for seed in seed_data:
                cc += 1
                c = Categoria()
                c.nome = seed["categoria"]
                db.session.add(c)
                for p in seed["produtos"]:
                    pc += 1
                    produto = Produto()
                    produto.nome = p["nome"]
                    produto.preco = p["preco"]
                    produto.estoque = random.randrange(-5, 60)
                    produto.ativo = random.random() < 0.85
                    produto.categoria = c
                    db.session.add(produto)
                db.session.commit()
            app.logger.info("Semeadura das tabelas concluída")
            app.logger.info(f"Adicionados {pc} produtos em {cc} categorias")

    @app.route("/")
    @app.route("/index")
    def index():
        return render_template("index.jinja", title="Página inicial")

    return app
