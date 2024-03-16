from functools import wraps

from flask import current_app, flash, redirect, url_for, request
from flask_login import current_user


def papeis_aceitos(*nomes_de_papeis):
    def wrapper(funcao_de_view):
        @wraps(funcao_de_view)
        def decorator(*args, **kwargs):
            from src.modules import login
            if not current_user.is_authenticated:
                flash(login.login_message, category=login.login_message_category)
                return redirect(url_for(login.login_view))
            if not current_user.tem_papeis(nomes_de_papeis):
                flash("Sem autorização para utilizar essa funcionalidade", category='warning')
                current_app.logger.debug(f"user: {current_user.email}, acesso não autorizado")
                return redirect(request.referrer if request.referrer else url_for('/'))

            return funcao_de_view(*args, **kwargs)

        return decorator

    return wrapper
