import json
import logging
import os
import random
import sys
import uuid
from pathlib import Path

from flask import Flask, render_template, request
from flask_login import user_logged_in

import src.routes.auth
import src.routes.categoria
import src.routes.produto
from src import utils
from src.models.usuario import User, Role
from src.models.categoria import Categoria
from src.models.produto import Produto
from src.modules import bootstrap, minify, db, csrf, login, mail


def create_app(config_filename: str = 'config.dev.json') -> Flask:
    app = Flask(__name__, instance_relative_config=True, static_folder='static', template_folder='templates')

    # Desativar as mensagens do servidor HTTP
    # https://stackoverflow.com/a/18379764
    # logging.getLogger('werkzeug').setLevel(logging.ERROR)

    # Quando em produção, fazer os ajustes para garantir que REMOTE_ADDR está correto
    # https://werkzeug.palletsprojects.com/en/3.0.x/middleware/proxy_fix/
    # https://werkzeug.palletsprojects.com/en/3.0.x/deployment/proxy_fix/

    if not Path(app.instance_path).is_dir():
        try:
            os.makedirs(app.instance_path)
        except OSError:
            pass

    # Definindo o nível de logging da aplicação
    app.logger.setLevel(logging.DEBUG)

    app.logger.debug("Carregando o arquivo de configuração %s" % config_filename)
    try:
        app.config.from_file(config_filename, load=json.load)
    except FileNotFoundError as e:
        app.logger.fatal("Arquivo \"%s\" não encontrado" % config_filename)
        app.logger.fatal("Exception: %s" % e)
        exit(1)

    mandatory_keys = [
        'APP_BASE_URL',
        'APP_MTA_MESSAGEID',
        'APP_NAME',
        'SECRET_KEY',
        'SQLALCHEMY_DATABASE_URI',
        'TIMEZONE',
    ]
    for key in mandatory_keys:
        if app.config.get(key, None) is None:
            app.logger.fatal("Necessário definir a chave \"%s\" no arquivo %s" % (key, config_filename))
            exit(1)

    app.logger.debug("Inicializando módulos básicos")
    bootstrap.init_app(app)
    if 'MINIFY' in app.config:
        if app.config.get('MINIFY'):
            minify.init_app(app)
    db.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    login.init_app(app)
    login.login_view = 'auth.login'
    login.login_message = "É necessário estar logado para acessar esta funcionalidade"
    login.login_message_category = 'warning'
    login.session_protection = 'strong'

    # Formatando as datas para horário local
    # https://stackoverflow.com/q/65359968
    app.jinja_env.filters['as_localtime'] = utils.as_localtime

    app.logger.debug("Registrando as blueprints")
    app.register_blueprint(src.routes.auth.bp)
    app.register_blueprint(src.routes.categoria.bp)
    app.register_blueprint(src.routes.produto.bp)

    with app.app_context():
        if not utils.existe_esquema(app):
            app.logger.fatal("Necessário fazer a migração/upgrade do banco")
            sys.exit(1)

        if Role.is_empty():
            papeis = ['Admin', 'Usuario']
            for nome_papel in papeis:
                db.session.add(Role(nome_papel))
                app.logger.info("Adicionando papel \"%s\"" % nome_papel)
            db.session.commit()

        if User.is_empty():
            usuarios = [
                {'nome': "Administrador",
                 'email': app.config.get('DEFAULT_ADMIN_EMAIL', 'admin@admin.com.br'),
                 'senha': "123",
                 'ativo': True,
                 'papeis': ['Admin', 'Usuario'],
                 },
                {'nome': "Usuario",
                 'email': app.config.get('DEFAULT_USER_EMAIL', 'user@user.com.br'),
                 'senha': "123",
                 'ativo': False,
                 'papeis': ['Usuario'],
                 },
            ]
            for usuario in usuarios:
                app.logger.info("Adicionando usuário (%s:%s)" % (usuario.get('email'), usuario.get('senha')))
                novo_usuario = User()
                novo_usuario.nome = usuario.get('nome')
                novo_usuario.email = usuario.get('email')
                novo_usuario.set_password(usuario.get('senha'))
                novo_usuario.email_validado = True
                novo_usuario.ativo = usuario.get('ativo')
                novo_usuario.dta_validacao_email = utils.timestamp()
                novo_usuario.usa_2fa = False
                for nome_papel in usuario.get('papeis'):
                    papel = Role.get_first_or_none_by('nome', nome_papel, casesensitive=False)
                    if not papel:
                        raise ValueError("Papel \"%s\" inexistente" % nome_papel)
                    novo_usuario.pertence_aos_papeis.append(papel)
                db.session.add(novo_usuario)
                db.session.commit()

        if Categoria.is_empty():
            from src.models.seed import seed_data
            app.logger.info("Semeando as tabelas")
            cc = pc = 0
            for seed in seed_data:
                cc += 1
                categoria = Categoria()
                categoria.nome = seed.get('categoria')
                db.session.add(categoria)
                for p in seed.get('produtos'):
                    pc += 1
                    produto = Produto()
                    produto.nome = p.get('nome')
                    produto.preco = p.get('preco')
                    produto.estoque = random.randrange(-5, 60)
                    produto.ativo = random.random() < 0.8
                    produto.categoria = categoria
                    db.session.add(produto)
                db.session.commit()
            app.logger.info("Semeadura das tabelas concluída")
            app.logger.info("Adicionados %d produtos em %d categorias" % (pc, cc))

    @user_logged_in.connect_via(app)
    def update_login_details(sender_app, user):
        remote_addr = request.remote_addr or None
        timestamp = utils.timestamp()

        login_anterior, login_atual = user.dta_acesso_atual, timestamp
        ip_anterior, ip_atual = user.ip_acesso_atual, remote_addr

        user.dta_ultimo_acesso = login_anterior or login_atual
        user.dta_acesso_atual = login_atual
        user.ip_ultimo_acesso = ip_anterior
        user.ip_acesso_atual = ip_atual

    @login.user_loader
    def load_user(user_id):
        try:
            auth_id = uuid.UUID(str(user_id))
        except ValueError:
            return None
        else:
            return User.get_by_id(auth_id)

    @app.route('/')
    @app.route('/index')
    def index():
        return render_template('index.jinja',
                               title="Página inicial")

    return app
