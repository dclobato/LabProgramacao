import random
import smtplib
import uuid
from base64 import b64encode
from hashlib import md5
from io import BytesIO
from time import time
from typing import Optional, Self, List

import email_validator
import jwt
import jwt.exceptions
import pyotp
from flask import current_app
from flask_login import UserMixin
from flask_mailman import EmailMessage
from qrcode.main import QRCode
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.types import Uuid, String, DateTime, Boolean, Integer
# noinspection PyPackageRequirements
from werkzeug.security import generate_password_hash, check_password_hash

from src.modules import db
from .base_mixin import TimestampMixin, BasicRepositoryMixin

users_roles = Table("usersroles", db.Model.metadata, Column("usuario_id", ForeignKey("usuarios.id"), primary_key=True),
                    Column("role_id", ForeignKey("roles.id"), primary_key=True))


class User(db.Model, TimestampMixin, BasicRepositoryMixin, UserMixin):
    __tablename__ = "usuarios"

    id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(60), nullable=False)
    email_normalizado: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    email_validado: Mapped[Boolean] = mapped_column(Boolean, default=False)
    dta_validacao_email: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)

    dta_ultimo_acesso: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    dta_acesso_atual: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    ip_ultimo_acesso: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ip_acesso_atual: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    usa_2fa: Mapped[Boolean] = mapped_column(Boolean, default=False)
    otp_secret: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    ultimo_otp: Mapped[Optional[str]] = mapped_column(String(6), nullable=True)
    dta_ativacao_2fa: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)

    lista_2fa_backup = relationship("Backup2FA",  # Type: Mapped[Optional[List[Backup2FA]]]
                                    back_populates="usuario", lazy="select", cascade="all, delete-orphan")

    pertence_aos_papeis: Mapped[List["Role"]] = relationship(secondary=users_roles,  # Type: Mapped[List[Role]]
                                                             lazy="select", back_populates="usuarios_no_papel",
                                                             cascade="all, delete")

    @property
    def otp_secret_formatted(self):
        return " ".join(self.otp_secret[i:i + 4] for i in range(0, len(self.otp_secret), 4))

    @property
    def get_b64encoded_qr_totp_uri(self) -> str:
        qr = QRCode(version=1, box_size=10, border=5)
        qr.add_data(self.get_totp_uri, optimize=0)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        buffered = BytesIO()
        img.save(buffered)
        return b64encode(buffered.getvalue()).decode("utf-8")

    @property
    def email(self) -> str:
        return self.email_normalizado

    @email.setter
    def email(self, value: str) -> None:
        # noinspection PyTypeChecker
        self.email_normalizado = email_validator.validate_email(value, check_deliverability=False).normalized.lower()

    @property
    def nomes_dos_papeis(self) -> list[str]:
        r = list()
        for papel in self.pertence_aos_papeis:
            r.append(papel.nome)
        return r

    @classmethod
    def get_by_email(cls, user_email) -> Self | None:
        user_email = email_validator.validate_email(user_email, check_deliverability=False).normalized.lower()
        return cls.get_first_or_none_by("email_normalizado", user_email)

    @property
    def get_totp_uri(self) -> str:
        return pyotp.totp.TOTP(self.otp_secret).provisioning_uri(name=self.email, issuer_name='App2024')

    @staticmethod
    def verify_jwt_token(token):
        try:
            payload = jwt.decode(token, key=current_app.config.get("SECRET_KEY"), algorithms=["HS256"])
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
        from flask import current_app
        payload = {"user": str(self.id), "action": action.lower(), "exp": time() + expires_in}
        return jwt.encode(payload=payload, key=current_app.config.get("SECRET_KEY"), algorithm="HS256")

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

    def send_email(self, subject: str = "Mensagem do sistema", body: str = "") -> bool:
        msg = EmailMessage()
        msg.to = [self.email]
        msg.subject = f"[{current_app.config.get("APP_NAME")}] {subject}"
        msg.body = body
        msg.extra_headers["Message-ID"] = f"{str(uuid.uuid4())}@{current_app.config.get('APP_MTA_MESSAGEID')}"
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
    usuario_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("usuarios.id"))

    usuario = relationship("User",  # Type: Mapped[User]
                           back_populates="lista_2fa_backup")


class Role(db.Model, BasicRepositoryMixin):
    __tablename__ = "roles"

    id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)

    usuarios_no_papel: Mapped[List["User"]] = relationship(secondary=users_roles,  # Type:
                                                           lazy="select", back_populates="pertence_aos_papeis",
                                                           viewonly=True)

    def __init__(self, _nome: str):
        # noinspection PyTypeChecker
        self.nome = _nome
