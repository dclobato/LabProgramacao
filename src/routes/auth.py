import datetime
from urllib.parse import urlsplit

import pytz
from flask import redirect, url_for, flash, request, render_template, Blueprint, current_app
from flask_login import current_user, login_user, login_required, logout_user

from src.forms.auth import LoginForm, SetNewPasswordForm, AskToResetPassword, RegistrationForm
from src.models.auth import User
from src.modules import db
from src.utils import get_user_by_email, enviar_email_reset_senha, enviar_email_novo_usuario

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        usuario = get_user_by_email(form.email.data)

        if usuario is None:
            flash('Email ou senha incorretos', category="warning")
            return redirect(url_for('auth.login'))
        if not usuario.check_password(form.password.data):
            flash('Email ou senha incorretos', category="warning")
            return redirect(url_for('auth.login'))
        if not usuario.email_validado:
            flash('Email ainda não confirmado', category="warning")
            return redirect(url_for('auth.login'))

        login_user(usuario, remember=form.remember_me.data)
        current_user.ultimo_acesso = datetime.datetime.now(tz=pytz.timezone('UTC'))
        db.session.commit()
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        flash(f'Usuario {usuario.email} logado', category="success")
        return redirect(next_page)
    return render_template('auth/login.jinja', title='Dados de acesso', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash(f'Sessão encerrada', category="success")
    return redirect(url_for('index'))


@bp.route('reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    usuario, action = User.verify_jwt_token(token)
    if usuario is None:
        flash('Usuário inválido', category="warning")
        return redirect(url_for('index'))
    if action == "reset_password":
        form = SetNewPasswordForm()
        if form.validate_on_submit():
            usuario.set_password(form.password.data)
            db.session.commit()
            flash('Sua senha foi redefinida!', category="success")
            return redirect(url_for('auth.login'))
        return render_template('auth/reset_password.jinja', title="Escolha uma nova senha", form=form)
    else:
        flash('Token inválido', category="warning")
        return redirect(url_for('index'))


@bp.route('/new_password/', methods=['GET', 'POST'])
def new_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = AskToResetPassword()
    if form.validate_on_submit():
        usuario = get_user_by_email(form.email.data)
        flash(f"Se houver uma conta com o email {form.email.data}, uma mensagems será enviada "
              f"com as instruções para redefinir a senha",
              category="success")
        if usuario:
            if not enviar_email_reset_senha(usuario.id):
                current_app.logger.warning(f"Email de reset de senha para o usuario {str(usuario.id)} não enviado")
            return redirect(url_for('auth.login'))
        else:
            current_app.logger.info(f"Pedido de reset de senha para usuario inexistente ({form.email.data})")
    return render_template('auth/new_password.jinja', title='Esqueci minha senha', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        usuario = User()
        usuario.nome = form.nome.data
        usuario.email = form.email.data
        usuario.set_password(form.password.data)
        usuario.email_validado = False
        db.session.add(usuario)
        db.session.flush()
        db.session.refresh(usuario)
        user_id = usuario.id
        db.session.commit()
        flash('Cadastro efetuado com sucesso. Confirme seu email antes de logar no sistema', category="success")
        if not enviar_email_novo_usuario(user_id):
            current_app.logger.warning(f"Email de ativação para para o usuario {str(user_id)} não enviado")
        return redirect(url_for('auth.login'))
    return render_template('auth/register.jinja', title='Cadastro de usuário', form=form)


@bp.route('/valida_email/<token>')
def valida_email(token):
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    usuario, action = User.verify_jwt_token(token)
    if usuario and not usuario.email_validado and action == "validate_email" :
        usuario.email_validado = True
        flash(f'Email {usuario.email} validado!', category="success")
        db.session.commit()
        return redirect(url_for('auth.login'))
    flash('Token inválido', category="warning")
    return redirect(url_for('index'))
