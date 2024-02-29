import werkzeug.exceptions
from flask import Blueprint, render_template, request, current_app, flash
from sqlalchemy.sql.operators import ilike_op

from src.models.categoria import Categoria
from src.modules import db

bp = Blueprint("categoria", __name__, url_prefix="/categoria")


@bp.route("/", methods=["GET"])
def lista():
    # noinspection PyPep8Naming
    MAXPERPAGE = int(current_app.config.get("MAX_PER_PAGE", 500))

    page = request.args.get("page", default=1, type=int)
    pp = request.args.get("pp", default=10, type=int)
    q = request.args.get("q", default=None, type=str)

    sentenca = db.select(Categoria)

    if pp > MAXPERPAGE:
        pp = MAXPERPAGE

    # Filtrar por parte do nome
    if q:
        sentenca = sentenca.filter(ilike_op(Categoria.nome, f"%{q}%"))

    sentenca = sentenca.order_by(Categoria.nome)

    try:
        rset_page = db.paginate(sentenca, page=page, per_page=pp,
                                max_per_page=MAXPERPAGE, error_out=True)
    except werkzeug.exceptions.NotFound as e:
        current_app.logger.warning(f"Exception: {e}")
        page = 1
        flash("Não existem registros na página solicitada. Apresentando primeira página", category='info')
        rset_page = db.paginate(sentenca, page=page, per_page=pp,
                                max_per_page=MAXPERPAGE, error_out=True)

    return render_template("categoria/lista.jinja",
                           rset_page=rset_page,
                           page=page,
                           pp=pp,
                           q=q,
                           title="Lista de categorias")
