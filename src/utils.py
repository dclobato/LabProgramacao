import datetime
import sys
from pathlib import Path

import pytz
from flask import Flask


# Formatando as datas para horário local
# https://stackoverflow.com/q/65359968
def as_localtime(value) -> str | datetime.date:
    import pytz
    from flask import current_app
    if not value:
        return "Sem registro"
    tz = current_app.config.get('TIMEZONE')
    try:
        formato = '%Y-%m-%d, %H:%M'
        utc = pytz.timezone('UTC')
        tz_aware_dt = utc.localize(value)
        local_dt = tz_aware_dt.astimezone(pytz.timezone(tz))
        return local_dt.strftime(formato)
    except Exception as e:
        current_app.logger.warning(f"as_localtime: Exception: {e}")
        return value


def timestamp():
    return datetime.datetime.now(tz=pytz.timezone('UTC'))


def existe_esquema(app: Flask) -> bool:
    # Se estivéssemos usando um SGBD, poderíamos consultar os metadados
    # do esquema com algo como a linha abaixo para o MariaDB/MySQL
    # SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'DBName'
    # Como o sqlite é um arquivo no sistema de arquivos, vamos simplesmente
    # verificar se o arquivo existe
    arquivo = Path(app.instance_path) / Path(app.config.get('SQLITE_DB_NAME', 'application_db.sqlite3'))
    return arquivo.is_file()
    # configurar o alembic
    #    alembic init instance/migrations
    #
    # ajustar o alembic.ini
    #    [alembic]
    #    sqlalchemy.url = sqlite+pysqlite:///instance/application_db.sqlite3
    #
    # ajustar o env.py (l21-22)
    #    from src.modules import Base
    #    target_metadata = Base.metadata
