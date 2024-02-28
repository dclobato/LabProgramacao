import uuid

from src.models import TimestampMixin
from src.modules import db

import sqlalchemy as sa
from sqlalchemy.types import Uuid, String


class Categoria(db.Model, TimestampMixin):
    __tablename__ = "categorias"

    id = sa.Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = sa.Column(String(60), nullable=False)
    lista_de_produtos = sa.orm.relationship("Produto",
                                            back_populates="categoria",
                                            lazy="selectin",
                                            cascade="all, delete-orphan")
