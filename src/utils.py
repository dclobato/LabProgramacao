import json
from base64 import b64encode
from datetime import date
from io import BytesIO

import email_validator
import requests
from qrcode.main import QRCode
from requests import RequestException


# Formatando as datas para horário local
# https://stackoverflow.com/q/65359968
def as_localtime(value) -> str | date:
    import pytz
    from flask import current_app
    tz = current_app.config.get("TIMEZONE")
    try:
        formato = "%Y-%m-%d, %H:%M"
        utc = pytz.timezone('UTC')
        tz_aware_dt = utc.localize(value)
        local_dt = tz_aware_dt.astimezone(pytz.timezone(tz))
        return local_dt.strftime(formato)
    except Exception as e:
        current_app.logger.warning(f"as_localtime: Exception: {e}")
        return value


def get_b64encoded_qr_image(data) -> str:
    qr = QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buffered = BytesIO()
    img.save(buffered)
    return b64encode(buffered.getvalue()).decode("utf-8")


def b64encode_image(data) -> str:
    return b64encode(data).decode("ascii")


def normalized_email(email: str, check_deliverability: bool = False) -> str:
    return email_validator.validate_email(email, check_deliverability=check_deliverability).normalized


def split_by(texto: str, size: int = 4, separador: str = ' '):
    return separador.join(texto[i:i + size] for i in range(0, len(texto), size))


# https://github.com/leogregianin/viacep-python/tree/main
class ViaCep:
    def __init__(self, cep):
        self.cep = cep

    def getDadosCep(self):
        url_api = f"http://www.viacep.com.br/ws/{self.cep}/json"
        try:
            req = requests.get(url_api)
            if req.status_code == 200:
                return (json.loads(req.text))
            else:
                return None
        except RequestException:
            return None
