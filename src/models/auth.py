import random
import uuid
from hashlib import md5
from time import time

import jwt
import jwt.exceptions
import pyotp
import sqlalchemy as sa
from flask_login import UserMixin
from sqlalchemy.types import Uuid, String, DateTime, Boolean, Integer
# noinspection PyPackageRequirements
from werkzeug.security import generate_password_hash, check_password_hash

from src.models import TimestampMixin
from src.modules import db


class User(db.Model, TimestampMixin, UserMixin):
    __tablename__ = "usuarios"

    id = sa.Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = sa.Column(String(60), nullable=False)
    email = sa.Column(String(60), nullable=False, unique=True)
    password_hash = sa.Column(String(256), nullable=False)
    email_validado = sa.Column(Boolean, default=False)
    dta_ultimo_acesso = sa.Column(DateTime, nullable=True)

    usa_2fa = sa.Column(Boolean, default=False)
    otp_secret = db.Column(String(32))
    dta_ativacao_2fa = sa.Column(DateTime, nullable=True)
    lista_2fa_backup = sa.orm.relationship("Backup2FA",
                                           back_populates="usuario",
                                           lazy="selectin",
                                           cascade="all, delete-orphan")

    @property
    def get_totp_uri(self) -> str:
        return pyotp.totp.TOTP(self.otp_secret).provisioning_uri(name=self.email, issuer_name='App2024')

    @staticmethod
    def verify_jwt_token(token):
        from src.utils import get_user_by_id
        from flask import current_app
        try:
            payload = jwt.decode(token,
                                 key=current_app.config.get("SECRET_KEY"),
                                 algorithms=["HS256"])
        except Exception as e:
            current_app.logger.error(f"JWT Token validation: {e}")
            return None, None
        else:
            user_id = uuid.UUID(payload.get("user", None))
            action = payload.get("action", None)

        return get_user_by_id(user_id), action

    def url_gravatar(self, size: int = 32) -> str:
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password) -> bool:
        return check_password_hash(self.password_hash, password)

    def create_jwt_token(self, action: str, expires_in: int = 600):
        from flask import current_app
        payload = {
            "user": str(self.id),
            "action": action.lower(),
            "exp": time() + expires_in
        }
        return jwt.encode(payload=payload,
                          key=current_app.config.get("SECRET_KEY"),
                          algorithm="HS256")

    def verify_totp(self, token) -> bool:
        totp = pyotp.TOTP(self.otp_secret)
        return totp.verify(token, valid_window=1)

    def generate_2fa_backup(self, quantos: int = 5) -> list[str]:
        # Remove os codigos anteriores
        for codigo in self.lista_2fa_backup:
            db.session.delete(codigo)
        # Gera novos códigos
        codigos = []
        for _ in range(quantos):
            codigo = "".join(random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
            codigos.append(codigo)
            backup2fa = Backup2FA()
            backup2fa.hash_codigo = generate_password_hash(codigo)
            self.lista_2fa_backup.append(backup2fa)
        return codigos

    def verify_totp_backup(self, token) -> bool:
        for codigo in self.lista_2fa_backup:
            if check_password_hash(codigo.hash_codigo, token):
                db.session.delete(codigo)
                return True
        return False


class Backup2FA(db.Model):
    __tablename__ = "backup2fa"

    id = sa.Column(Integer, primary_key=True)
    hash_codigo = sa.Column(String(256), nullable=False)
    usuario_id = sa.Column(Uuid(as_uuid=True), sa.ForeignKey("usuarios.id"))

    usuario = sa.orm.relationship("User", back_populates="lista_2fa_backup")
