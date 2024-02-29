import uuid

import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.types import Uuid, String

from src.models import TimestampMixin
from src.modules import db


class Categoria(db.Model, TimestampMixin):
    __tablename__ = "categorias"

    id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(60), nullable=False)
    lista_de_produtos = sa.orm.relationship("Produto",
                                            back_populates="categoria",
                                            lazy="selectin",
                                            cascade="all, delete-orphan")
