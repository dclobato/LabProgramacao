from flask import Blueprint, render_template, flash, redirect, url_for, request, Response
from flask_login import login_required

from src.forms.produto import NovoProdutoForm
from src.models.categoria import Categoria
from src.models.produto import Produto
from src.modules import db
from src.utils import get_tuples, b64encode_image

bp = Blueprint("produto", __name__, url_prefix="/produto")


@bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    form = NovoProdutoForm()
    form.categoria.choices = get_tuples(Categoria, db)

    if form.validate_on_submit():
        categoria = db.session.get(Categoria, form.categoria.data)
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
    produto = db.session.get(Produto, id_produto)
    if produto is None:
        return Response(status=404)
    imagem_content, imagem_type = produto.imagem
    return Response(imagem_content, mimetype=imagem_type)


@bp.route("/<uuid:id_produto>/thumbnail", methods=["GET"])
@bp.route("/<uuid:id_produto>/thumbnail/<int:max_size>", methods=["GET"])
@login_required
def thumbnail(id_produto, max_size: int = 64):
    produto = db.session.get(Produto, id_produto)
    if produto is None:
        return Response(status=404)
    imagem_content, imagem_type = produto.thumbnail(max_size=max_size)
    return Response(imagem_content, mimetype=imagem_type)
