import werkzeug.exceptions
from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for
from flask_login import login_required

from src.role_management import papeis_aceitos
from src.forms.categoria import NovoCategoriaForm, EditCategoriaForm
from src.models.categoria import Categoria
from src.modules import db

bp = Blueprint("categoria", __name__, url_prefix="/admin/categoria")


@bp.route("/", methods=["GET"])
@login_required
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
        sentenca = sentenca.filter(Categoria.nome.ilike(f"%{q}%"))

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


@bp.route("/novo", methods=["GET", "POST"])
@login_required
@papeis_aceitos("Admin")
def novo():
    form = NovoCategoriaForm()
    if form.validate_on_submit():
        categoria = Categoria()
        categoria.nome = form.nome.data
        db.session.add(categoria)
        db.session.commit()
        flash(message=f"Categoria '{form.nome.data}' adicionada", category="success")
        return redirect(url_for('categoria.lista'))
    return render_template("render_simple_slim_form.jinja",
                           title="Nova categoria",
                           form=form)


@bp.route("/edit/<uuid:id_categoria>", methods=["GET", "POST"])
@login_required
@papeis_aceitos("Admin")
def edit(id_categoria):
    categoria = Categoria.get_by_id(id_categoria)
    if categoria is None:
        flash("Categoria inexistente!", category='danger')
        return redirect(url_for('categoria.lista'))

    form = EditCategoriaForm(request.values, obj=categoria)
    if form.validate_on_submit():
        categoria.nome = form.nome.data
        db.session.commit()
        flash(message="Categoria alterada!", category='success')
        return redirect(url_for("categoria.lista"))

    return render_template("categoria/edit.jinja", form=form, categoria=categoria, title="Alterar categoria")


@bp.route("/remove/<uuid:id_categoria>", methods=["GET", "POST"])
@login_required
@papeis_aceitos("Admin")
def remove(id_categoria):
    # categoria = get_by_id(Categoria, id_categoria)
    categoria = Categoria.get_by_id(id_categoria)
    if categoria is None:
        flash("Categoria inexistente!", category='danger')
        return redirect(url_for('categoria.lista'))

    if request.method == "POST":  # confirmação da remoção
        flash(message=f"Categoria '{categoria.nome}' e produtos removidos!", category='success')
        db.session.delete(categoria)
        db.session.commit()
        return redirect(url_for("categoria.lista"))

    return render_template("categoria/remove.jinja", categoria=categoria, title="Remover categoria")
