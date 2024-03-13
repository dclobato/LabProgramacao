import random
import uuid
from hashlib import md5
from time import time
from typing import Optional, List, Self

import jwt
import jwt.exceptions
import pyotp
import sqlalchemy as sa
from flask import current_app
from flask_login import UserMixin
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.types import Uuid, String, DateTime, Boolean, Integer
from werkzeug.security import generate_password_hash, check_password_hash

from src.modules import db
from . import TimestampMixin
from .mixins import OperationsMixin

# tabelas associativas
users_roles = sa.Table("usersroles", db.Model.metadata,
                       sa.Column("usuario_id",
                                 sa.ForeignKey("usuarios.id"), primary_key=True),
                       sa.Column("role_id",
                                 sa.ForeignKey("roles.id"), primary_key=True)
                       )


class User(db.Model, TimestampMixin, UserMixin, OperationsMixin):
    __tablename__ = "usuarios"

    id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(60), nullable=False)
    email: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    email_validado: Mapped[Boolean] = mapped_column(Boolean, default=False)

    dta_ultimo_acesso: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    dta_acesso_atual: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    ip_ultimo_acesso: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ip_acesso_atual: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    usa_2fa: Mapped[Boolean] = mapped_column(Boolean, default=False)
    otp_secret: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    dta_ativacao_2fa: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    ultimo_otp: Mapped[Optional[str]] = mapped_column(String(6), nullable=True)

    lista_2fa_backup = sa.orm.relationship("Backup2FA",
                                           back_populates="usuario",
                                           lazy="selectin",
                                           cascade="all, delete-orphan")

    pertence_aos_papeis: Mapped[List["Role"]] = sa.orm.relationship(secondary=users_roles,
                                                                    lazy="select",
                                                                    back_populates="usuarios_no_papel",
                                                                    cascade="all, delete")

    @property
    def nomes_dos_papeis(self) -> list[str] | None:
        r = list()
        for papel in self.pertence_aos_papeis:
            r.append(papel.nome)
        return r if len(r) > 0 else None

    @classmethod
    def get_by_email(cls, user_email) -> Self | None:
        from src.utils import normalized_email
        user_email = normalized_email(user_email)
        return db.session.execute(db.select(User).where(User.email == user_email).limit(1)).scalar_one_or_none()

    @property
    def get_totp_uri(self) -> str:
        totp = pyotp.TOTP(self.otp_secret)
        return totp.provisioning_uri(name=self.email,
                                     issuer_name=current_app.config.get("APP_NAME"))

    @staticmethod
    def verify_jwt_token(token):
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

        return User.get_by_id(user_id), action

    def url_gravatar(self, size: int = 32) -> str:
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def set_password(self, password):
        # noinspection PyTypeChecker
        self.password_hash = generate_password_hash(password)

    def check_password(self, password) -> bool:
        return check_password_hash(self.password_hash, password)

    def create_jwt_token(self, action: str, expires_in: int = 600):
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

    def send_email(self, subject: str = "[Mensagem do sistema]", body: str = "") -> bool:
        import smtplib
        from flask_mailman import EmailMessage
        msg = EmailMessage()
        msg.to = [self.email]
        msg.subject = f"[{current_app.config.get("APP_NAME")}] {subject}"
        msg.body = body
        try:
            msg.send()
        except smtplib.SMTPException:
            return False
        else:
            return True

    # Based on Flask-user/flask_user/user_mixin.py#L59
    def tem_papeis(self, *papeis_necessarios):
        # tem_papeis('a', ('b', 'c'), d)
        # traduz para:
        # usuario tem papel 'a' AND (papel 'b' OR papel 'c') AND papel 'd'
        papeis_do_usuario = self.nomes_dos_papeis
        current_app.logger.debug(f"Papeis do usuario: {papeis_do_usuario}")
        current_app.logger.debug(f"Papeis necessarios: {papeis_necessarios}")
        for papel in papeis_necessarios:
            current_app.logger.debug(f"Papel: {papel}, tipo {type(papel)}")
            if isinstance(papel, (list, tuple)):
                tupla_de_nomes_de_papel = papel
                autorizado = False
                for nome_de_papel in tupla_de_nomes_de_papel:
                    current_app.logger.debug(f"lista - Testando '{nome_de_papel}' contra '{papeis_do_usuario}'")
                    if nome_de_papel in papeis_do_usuario:
                        autorizado = True
                        break
                if not autorizado:
                    return False
            else:
                nome_de_papel = papeis_necessarios
                current_app.logger.debug(f"single - Testando '{nome_de_papel}' contra '{papeis_do_usuario}'")
                if nome_de_papel not in papeis_do_usuario:
                    return False
        return True


class Backup2FA(db.Model):
    __tablename__ = "backup2fa"

    id: Mapped[Integer] = mapped_column(Integer, primary_key=True)
    hash_codigo: Mapped[str] = mapped_column(String(256), nullable=False)
    usuario_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), sa.ForeignKey("usuarios.id"))

    usuario = sa.orm.relationship("User",
                                  lazy="select",
                                  back_populates="lista_2fa_backup")


class Role(db.Model, OperationsMixin):
    __tablename__ = "roles"

    id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)

    usuarios_no_papel: Mapped[List["User"]] = sa.orm.relationship(secondary=users_roles,
                                                                  lazy="select",
                                                                  back_populates="pertence_aos_papeis",
                                                                  viewonly=True)

    # noinspection PyTypeChecker
    def __init__(self, _nome: str):
        self.nome = _nome
