import uuid
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.types import Uuid, String, DateTime, Boolean, Integer, DECIMAL

from src.modules import db
from .mixins import OperationsMixin


class Pedido(db.Model, OperationsMixin):
    __tablename__ = "pedidos"

    id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    pedido_concluido: Mapped[Boolean] = mapped_column(Boolean, default=False)
    dta_pedido: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    dta_envio: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    valor_produtos: Mapped[Optional[DECIMAL]] = mapped_column(DECIMAL(10, 2), default=0.00)
    valor_frete: Mapped[Optional[DECIMAL]] = mapped_column(DECIMAL(10, 2), default=0.00)

    usuario_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), sa.ForeignKey("usuarios.id"))
    endereco_id: Mapped[Optional[Uuid]] = mapped_column(Uuid(as_uuid=True), sa.ForeignKey("enderecos.id"))

    usuario = sa.orm.relationship("User",
                                  lazy="select",
                                  back_populates="lista_de_pedidos")

    endereco = sa.orm.relationship("Endereco",
                                   lazy="select",
                                   back_populates="lista_de_pedidos")

    lista_de_produtos = sa.orm.relationship("ItemPedido",
                                            back_populates="pedido",
                                            lazy="select",
                                            cascade="all, delete-orphan")


class Endereco(db.Model, OperationsMixin):
    __tablename__ = "enderecos"

    id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    usuario_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), sa.ForeignKey("usuarios.id"))
    nome: Mapped[str] = mapped_column(String(15), nullable=False, default="Principal")
    destinatario: Mapped[str] = mapped_column(String(60), nullable=False)
    destinatario_logradouro: Mapped[str] = mapped_column(String(60), nullable=False)
    destinatario_numero: Mapped[str] = mapped_column(String(10), nullable=False)
    destinatario_complemento: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    destinatario_bairro: Mapped[str] = mapped_column(String(30), nullable=False)
    destinatario_cidade: Mapped[str] = mapped_column(String(45), nullable=False)
    destinatario_uf: Mapped[str] = mapped_column(String(2), nullable=False)
    destinatario_cep: Mapped[str] = mapped_column(String(9), nullable=False)

    usuario = sa.orm.relationship("User",
                                  lazy="select",
                                  back_populates="lista_de_enderecos")


class ItemPedido(db.Model, OperationsMixin):
    __tablename__ = "itenspedido"

    id_pedido: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True),
                                            sa.ForeignKey("pedidos.id"),
                                            primary_key=True)
    id_produto: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True),
                                             sa.ForeignKey("produtos.id"),
                                             primary_key=True)

    quantidade: Mapped[Integer] = mapped_column(Integer, default=0)
    valor_unitario: Mapped[Optional[DECIMAL]] = mapped_column(DECIMAL(10, 2), default=0.00)

    pedido = sa.orm.relationship("Pedido",
                                 lazy="select",
                                 back_populates="lista_de_produtos")

    produto = sa.orm.relationship("Produto",
                                  lazy="select",
                                  back_populates="lista_de_pedidos")
