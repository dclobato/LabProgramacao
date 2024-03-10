from flask import Blueprint, render_template, flash, redirect, url_for, request, Response, abort, current_app
from flask_login import login_required

from src.role_management import papeis_aceitos
from src.forms.produto import NovoProdutoForm
from src.models.categoria import Categoria
from src.models.produto import Produto
from src.modules import db
from src.utils import b64encode_image

bp = Blueprint("produto", __name__, url_prefix="/admin/produto")


@bp.route("/novo", methods=["GET", "POST"])
@login_required
@papeis_aceitos("Admin")
def novo():
    if Categoria.is_empty():
        flash("Não há categorias cadastradas. Impossível cadastrar um produto", category="error")
        return redirect(url_for("index"))

    form = NovoProdutoForm()
    form.categoria.choices = Categoria.get_tuples_id_atributo()
    if not form.categoria.choices:
        current_app.logger.fatal(f"Problema na criação das tuplas de categoria")
        abort(500)

    if form.validate_on_submit():
        categoria = Categoria.get_by_id(form.categoria.data)
        if categoria is None:
            flash("Categoria inválida", category='info')
            return redirect(url_for("index"))

        produto = Produto()
        produto.nome = form.nome.data
        produto.preco = form.preco.data
        produto.ativo = form.ativo.data
        produto.categoria = categoria
        if form.foto_raw.data:
            produto.possui_foto = True
            produto.foto_base64 = b64encode_image(request.files[form.foto_raw.name].read())
            produto.foto_mime = request.files[form.foto_raw.name].mimetype
        else:
            produto.possui_foto = False
            produto.foto_base64 = None
            produto.foto_mime = None
        db.session.add(produto)
        db.session.commit()
        flash(message=f"Produto '{form.nome.data}' adicionado", category="success")
        return redirect(url_for("index"))
    return render_template("render_simple_form.jinja",
                           title="Nova categoria",
                           form=form)


@bp.route("/<uuid:id_produto>/imagem", methods=["GET"])
@login_required
def imagem(id_produto):
    produto = Produto.get_by_id(id_produto)
    if produto is None:
        return Response(status=404)
    imagem_content, imagem_type = produto.imagem
    return Response(imagem_content, mimetype=imagem_type)


@bp.route("/<uuid:id_produto>/thumbnail", methods=["GET"])
@bp.route("/<uuid:id_produto>/thumbnail/<int:max_size>", methods=["GET"])
@login_required
def thumbnail(id_produto, max_size: int = 64):
    produto = Produto.get_by_id(id_produto)
    if produto is None:
        return Response(status=404)
    imagem_content, imagem_type = produto.thumbnail(max_size=max_size)
    return Response(imagem_content, mimetype=imagem_type)
