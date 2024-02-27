import uuid
from typing import Any

from flask import render_template, current_app
from flask_mailman import EmailMessage
from src.models.auth import User
from src.modules import db


def get_user_by_id(user_id) -> User | None:
    try:
        auth_id = uuid.UUID(str(user_id))
    except ValueError:
        return None
    else:
        return db.session.execute(db.select(User).where(User.id == auth_id).limit(1)).scalar()


def get_user_by_email(user_email) -> User | None:
    return db.session.execute(db.select(User).where(User.email == user_email).limit(1)).scalar()


def enviar_email_reset_senha(user_id: uuid.UUID) -> bool:
    usuario = get_user_by_id(user_id)
    if usuario is None:
        return False

    msg = EmailMessage()
    msg.to = [usuario.email]
    msg.subject = "[App2024] Mude a sua senha"
    msg.body = render_template("auth/email/password-reset-email.jinja",
                               user=usuario,
                               token=usuario.create_jwt_token("reset_password"),
                               host=current_app.config.get("APP_BASE_URL", "http://127.0.0.1:5000"))
    msg.send(fail_silently=True)
    return True
