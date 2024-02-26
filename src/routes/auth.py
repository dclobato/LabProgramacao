import datetime
from urllib.parse import urlsplit

import pytz
from flask import redirect, url_for, flash, request, render_template, Blueprint
from flask_login import current_user, login_user, login_required, logout_user

from src.forms.auth import LoginForm
from src.models.auth import User
from src.modules import db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        usuario = db.session.scalar(db.select(User).where(User.email == form.email.data))

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
