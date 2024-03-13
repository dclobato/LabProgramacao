import uuid
from typing import Self

import sqlalchemy as sa
from sqlalchemy import func

from src.modules import db


class OperationsMixin:

    @classmethod
    def is_empty(cls) -> bool:
        return not db.session.execute(sa.select(cls).limit(1)).scalar_one_or_none()

    @classmethod
    def get_tuples_id_atributo(cls,
                               atributo: str = "nome") -> list[tuple[str, str]] | None:
        if hasattr(cls, atributo):
            rset = db.session.execute(sa.select(cls).order_by(getattr(cls, atributo))).scalars()
            rtuples = [(str(i.id), str(getattr(i, atributo))) for i in rset]
        else:
            rtuples = None
        return rtuples

    @classmethod
    def get_by_id(cls,
                  cls_id) -> Self | None:
        try:
            cls_id = uuid.UUID(str(cls_id))
        except ValueError:
            cls_id = cls_id
        return db.session.get(cls, cls_id)

    @classmethod
    def get_first_or_none_by(cls,
                             atributo: str, valor: str | int | uuid.UUID,
                             casesensitive: bool = True) -> Self | None:
        registro = None
        if hasattr(cls, atributo):
            if casesensitive:
                registro = (db.session.execute(sa.select(cls).
                                               where(getattr(cls, atributo) == valor).
                                               limit(1)).scalar_one_or_none())
            else:
                if isinstance(valor, str):
                    # noinspection PyTypeChecker
                    registro = (db.session.execute(sa.select(cls).
                                                   where(func.lower(getattr(cls, atributo)) == func.lower(valor)).
                                                   limit(1)).scalar_one_or_none())
                else:
                    raise TypeError(f"Para operação case insensitive, o atributo '{atributo}' deve ser da classe str")
        return registro
