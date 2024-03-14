from urllib.parse import urlsplit

import pyotp
from flask import redirect, url_for, flash, request, render_template, Blueprint, current_app
from flask_login import current_user, login_user, login_required, logout_user

from src import utils
from src.forms.auth import LoginForm, SetNewPasswordForm, AskToResetPassword, RegistrationForm, ProfileForm, \
    Read2FACodeForm
from src.models.usuario import User, Role
from src.modules import db

bp = Blueprint("auth", __name__, url_prefix="/admin/user")


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        usuario = User.get_by_email(form.email.data)

        if usuario is None:
            flash('Email ou senha incorretos', category="warning")
            return redirect(url_for('auth.login'))
        if not usuario.check_password(form.password.data):
            flash('Email ou senha incorretos', category="warning")
            return redirect(url_for('auth.login'))
        if not usuario.email_validado:
            flash('Email ainda não confirmado', category="warning")
            return redirect(url_for('auth.login'))
        if usuario.usa_2fa:
            flash(f"Conclua o login para o usuário {usuario.email}", category="info")
            return redirect(url_for('auth.get2fa', user_id=usuario.id, remember_me=bool(form.remember_me.data),
                                    next=request.args.get('next')))
        login_user(usuario, remember=form.remember_me.data)
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
        return render_template('render_simple_slim_form.jinja', title="Escolha uma nova senha", form=form)
    else:
        flash('Token inválido', category="warning")
        return redirect(url_for('index'))


@bp.route('/new_password/', methods=['GET', 'POST'])
def new_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = AskToResetPassword()
    if form.validate_on_submit():
        email = form.email.data
        usuario = User.get_by_email(email)
        flash(f"Se houver uma conta com o email {email}, uma mensagems será enviada "
              f"com as instruções para redefinir a senha", category="success")
        if usuario:
            body = render_template("auth/email/password-reset-email.jinja", user=usuario,
                                   token=usuario.create_jwt_token("reset_password"),
                                   host=current_app.config.get("APP_BASE_URL"))
            if not usuario.send_email(subject="Altere a sua senha", body=body):
                current_app.logger.warning(f"Email de reset de senha para o usuario {str(usuario.id)} não enviado")
            return redirect(url_for('auth.login'))
        else:
            current_app.logger.info(f"Pedido de reset de senha para usuario inexistente ({email})")
    return render_template('render_simple_slim_form.jinja', title='Esqueci minha senha', form=form)


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
        usuario.usa_2fa = False
        usuario.pertence_aos_papeis.append(Role.get_first_or_none_by("nome", "Usuario", casesensitive=False))
        db.session.add(usuario)
        db.session.flush()
        db.session.refresh(usuario)
        body = render_template("auth/email/confirmation-email.jinja", user=usuario,
                               token=usuario.create_jwt_token("validate_email"),
                               host=current_app.config.get("APP_BASE_URL"))
        if not usuario.send_email(subject="Ative a sua conta", body=body):
            current_app.logger.warning(f"Email de ativação para para o usuario {str(usuario.id)} não enviado")
        db.session.commit()
        flash('Cadastro efetuado com sucesso. Confirme seu email antes de logar no sistema', category="success")
        return redirect(url_for('auth.login'))
    return render_template('render_simple_form.jinja', title='Cadastro de usuário', form=form)


@bp.route('/valida_email/<token>')
def valida_email(token):
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    usuario, action = User.verify_jwt_token(token)
    if usuario and not usuario.email_validado and action == "validate_email":
        usuario.email_validado = True
        usuario.dta_validacao_email = utils.timestamp()
        flash(f'Email {usuario.email} validado!', category="success")
        db.session.commit()
        return redirect(url_for('auth.login'))
    flash('Token inválido', category="warning")
    return redirect(url_for('index'))


@bp.route("/profile/", methods=['GET', 'POST'])
@login_required
def user():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.nome = form.nome.data
        if form.usa_2fa.data:
            if not current_user.usa_2fa:
                current_user.otp_secret = pyotp.random_base32()
                db.session.commit()
                flash("Alteração efetuadas. Conclua ativação da autenticação em dois fatores", "success")
                return redirect(url_for("auth.enable_2fa"))
        else:
            if current_user.usa_2fa:
                current_user.usa_2fa = False
                current_user.otp_secret = None
                current_user.ultimo_otp = None
                current_user.dta_ativacao_2fa = None
                if len(current_user.lista_2fa_backup) > 0:
                    for codigo in current_user.lista_2fa_backup:
                        db.session.delete(codigo)
                    flash("Códigos de autenticação reservas foram removidos", category="info")
        db.session.commit()
        flash(message="Alterações efetuadas", category='success')
        return redirect(url_for("auth.user"))
    return render_template("auth/user.jinja", title="Perfil do usuário", form=form)


@bp.route("/enable_2fa/", methods=['GET', 'POST'])
@login_required
def enable_2fa():
    if current_user.usa_2fa:
        flash("Configuração já efetuada. Para alterar, desative e reative a autenticação em dois fatores",
              category="info")
        return redirect(url_for("auth.user"))
    form = Read2FACodeForm()
    if request.method == 'POST' and form.is_submitted():
        if current_user.verify_totp(str(form.codigo.data)):
            # noinspection PyBroadException
            try:
                current_user.usa_2fa = True
                current_user.dta_ativacao_2fa = utils.timestamp()
                codigos = current_user.generate_2fa_backup(10)
                db.session.commit()
                flash("Autenticação em dois fatores ativada.", "success")
                return render_template("auth/show_2fa_backup.jinja", codigos=codigos,
                                       title="Códigos reserva para autenticação")
            except Exception:
                current_user.usa_2fa = False
                current_user.otp_secret = None
                current_user.dta_ativacao_2fa = None
                db.session.commit()
                flash("Problema da ativação da autenticação em dois fatores", "danger")
                return redirect(url_for("auth.user"))
        else:
            flash("O código informado está incorreto. Tente novamente.", "warning")
            return redirect(url_for("auth.enable_2fa"))
    imagem = current_user.get_b64encoded_qr_totp_uri
    return render_template("auth/enable_2fa.jinja", title="Ativação da autenticação em dois fatores", form=form,
                           imagem=imagem, token=current_user.otp_secret_formatted)


@bp.route('/get2fa/<uuid:user_id>', methods=['GET', 'POST'])
def get2fa(user_id):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    remember_me = request.args.get('remember_me')
    next_page = request.args.get('next')

    form = Read2FACodeForm()
    if form.validate_on_submit():
        usuario = User.get_by_id(user_id)
        if usuario is None:
            return redirect(url_for('auth.login'))
        token = str(form.codigo.data)
        if usuario.usa_2fa:
            if usuario.verify_totp(token=token) or usuario.verify_totp_backup(token=token):
                login_user(usuario, remember=bool(remember_me))
                usuario.ultimo_otp = token
                db.session.commit()
                if not next_page or urlsplit(next_page).netloc != '':
                    next_page = url_for('index')
                flash(f'Usuario {usuario.email} logado', category="success")
                return redirect(next_page)
            else:
                flash("Código incorreto", category="warning")
    return render_template('render_simple_slim_form.jinja', title='Autenticação em dois fatores', form=form)
