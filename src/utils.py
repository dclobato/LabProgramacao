import datetime

import pytz


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
