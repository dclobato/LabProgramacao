import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid, String, DECIMAL, Integer, Boolean

from src.models import TimestampMixin
from src.modules import db


class Produto(db.Model, TimestampMixin):
    __tablename__ = "produtos"

    id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    preco: Mapped[DECIMAL] = mapped_column(DECIMAL(10, 2), default=0.00)
    estoque: Mapped[Integer] = mapped_column(Integer, default=0)
    ativo: Mapped[Boolean] = mapped_column(Boolean, default=True)
    categoria_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), sa.ForeignKey("categorias.id"))

    categoria = sa.orm.relationship("Categoria",
                                    back_populates="lista_de_produtos")
