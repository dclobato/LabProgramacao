from flask import Blueprint, render_template
from flask_login import login_required, current_user

bp = Blueprint("backend", __name__, url_prefix="/backend")


@bp.route("/enderecos", methods=["GET"])
@login_required
def lista_enderecos():
    lst_enderecos = current_user.lista_de_enderecos

    return render_template("backend/enderecos_lista.jinja",
                           rset=lst_enderecos,
                           title="Endereços do usuário")


@bp.route("/enderecos/edit/<uuid:id_endereco>", methods=["GET", "POST"])
@login_required
def edita_endereco(id_endereco):
    pass


@bp.route("/enderecos/delete/<uuid:id_endereco>", methods=["GET", "POST"])
@login_required
def remove_endereco(id_endereco):
    pass
