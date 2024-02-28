import uuid

from src.models import TimestampMixin
from src.modules import db

import sqlalchemy as sa
from sqlalchemy.types import Uuid, String, DECIMAL, Integer, Boolean


class Produto(db.Model, TimestampMixin):
    __tablename__ = "produtos"

    id = sa.Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = sa.Column(String(100), nullable=False)
    preco = sa.Column(DECIMAL(10, 2), default=0.00)
    estoque = sa.Column(Integer, default=0)
    ativo = sa.Column(Boolean, default=True)
    categoria_id = sa.Column(Uuid(as_uuid=True), sa.ForeignKey("categorias.id"))

    categoria = sa.orm.relationship("Categoria",
                                    back_populates="lista_de_produtos")
