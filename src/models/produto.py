import io
import uuid
from base64 import b64decode
from typing import Optional

import sqlalchemy as sa
from PIL import Image
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid, String, DECIMAL, Integer, Boolean, Text

from src.modules import db
from . import TimestampMixin
from .mixins import OperationsMixin


class Produto(db.Model, TimestampMixin, OperationsMixin):
    __tablename__ = "produtos"

    id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    preco: Mapped[DECIMAL] = mapped_column(DECIMAL(10, 2), default=0.00)
    estoque: Mapped[Integer] = mapped_column(Integer, default=0)
    ativo: Mapped[Boolean] = mapped_column(Boolean, default=True)
    foto_base64: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    foto_mime: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    possui_foto: Mapped[Boolean] = mapped_column(Boolean, default=False)
    categoria_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), sa.ForeignKey("categorias.id"))

    categoria = sa.orm.relationship("Categoria",
                                    lazy="select",
                                    back_populates="lista_de_produtos")

    def thumbnail(self, max_size: int = 64) -> (bytes, str):
        saida = io.BytesIO()
        max_size = min(max_size, 128)
        if not self.foto_base64 or not self.possui_foto or not self.foto_mime:
            entrada = Image.new("RGB", (max_size, max_size), (128, 128, 128))
            formato = "PNG"
            mime_type = "image/png"
        else:
            entrada = Image.open(io.BytesIO(b64decode(self.foto_base64)))
            formato = entrada.format
            (largura, altura) = entrada.size
            fator_escala = max(max_size / largura, max_size / altura)
            novo_tamanho = (int(largura * fator_escala), int(altura * fator_escala))
            entrada.thumbnail(novo_tamanho)
            mime_type = self.foto_mime
        entrada.save(saida, format=formato)
        return saida.getvalue(), mime_type

    @property
    def imagem(self) -> (bytes, str):
        if not self.foto_base64 or not self.possui_foto or not self.foto_mime:
            saida = io.BytesIO()
            entrada = Image.new("RGB", (480, 480), (128, 128, 128))
            formato = "PNG"
            entrada.save(saida, format=formato)
            data = saida.getvalue()
            mime_type = "image/png"
        else:
            data = b64decode(self.foto_base64)
            mime_type = self.foto_mime
        return data, mime_type
