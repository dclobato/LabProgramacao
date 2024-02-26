import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import DateTime


class Base(DeclarativeBase):
    # Se houver atributo comum a todas as classes, pode adicionar aqui,
    # que serão incluidas nas classes filhas, e como atributos no BD
    pass


class TimestampMixin:
    """
    Um mixin para incluir data de cadastro e data de alteração em classes
    """
    dta_cadastro = sa.Column(DateTime, server_default=sa.func.now(), nullable=False)
    dta_atualizacao = sa.Column(DateTime, onupdate=sa.func.now(), default=sa.func.now(), nullable=False)
