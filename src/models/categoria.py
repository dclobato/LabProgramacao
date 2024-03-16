import uuid

from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.types import Uuid, String

from src.modules import db
from .base_mixin import TimestampMixin, BasicRepositoryMixin


class Categoria(db.Model, TimestampMixin, BasicRepositoryMixin):
    __tablename__ = 'categorias'

    id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(60), nullable=False)

    lista_de_produtos = relationship('Produto',  # Type: Mapped[Optional[List[Produto]]]
                                     back_populates='categoria',
                                     lazy='select',
                                     cascade='all, delete-orphan')
