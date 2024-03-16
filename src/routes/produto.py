import uuid

from werkzeug.exceptions import NotFound
from base64 import b64encode

from flask import Blueprint, render_template, flash, redirect, url_for, request, Response, current_app, abort
from flask_login import login_required

from src.role_management import papeis_aceitos
from src.forms.produto import NovoProdutoForm, EditProdutoForm
from src.models.produto import Produto
from src.models.categoria import Categoria
from src.modules import db

bp = Blueprint('produto', __name__, url_prefix='/admin/produto')


@bp.route('/', methods=['GET'])
@login_required
def lista():
    # noinspection PyPep8Naming
    MAXPERPAGE = int(current_app.config.get('MAX_PER_PAGE', 500))

    page = request.args.get('page', default=1, type=int)
    pp = request.args.get('pp', default=10, type=int)
    q = request.args.get('q', default="", type=str)
    a = request.args.get('a', default='off', type=str)
    c = request.args.get('c', default="", type=str)

    sentenca = db.select(Produto)

    if pp > MAXPERPAGE:
        pp = MAXPERPAGE

    # Filtrar por parte do nome
    if q != "":
        sentenca = sentenca.filter(Produto.nome.ilike(f"%{q}%"))

    # Filtrar por categoria
    if c != "":
        try:
            c = uuid.UUID(str(c))
        except ValueError:
            flash("Categoria inexistente!", category='warning')
            c = ""
            pass
        else:
            sentenca = sentenca.filter_by(categoria_id=c)

    # Filtrar por inativos
    try:
        assert a in ('on', 'off'), f"Parâmetro a inválido: {a}"
    except AssertionError as e:
        current_app.logger.warning(f"Exception: {e}")
        a = 'off'
    finally:
        if a == 'on':
            sentenca = sentenca.filter_by(ativo=0)

    sentenca = sentenca.order_by(Produto.nome)

    try:
        rset_page = db.paginate(sentenca, page=page, per_page=pp, max_per_page=MAXPERPAGE, error_out=True)
    except NotFound as e:
        current_app.logger.warning(f"Exception: {e}")
        page = 1
        flash("Não existem registros na página solicitada. Apresentando primeira página", category='info')
        rset_page = db.paginate(sentenca, page=page, per_page=pp, max_per_page=MAXPERPAGE, error_out=True)

    return render_template('produto/lista.jinja',
                           rset_page=rset_page,
                           page=page,
                           pp=pp,
                           q=q,
                           c=str(c),
                           a=a,
                           categorias=Categoria.get_tuples_id_atributo(),
                           title="Lista de produtos")


@bp.route('/novo', methods=['GET', 'POST'])
@login_required
@papeis_aceitos('Admin')
def novo():
    if Categoria.is_empty():
        flash("Não há categorias cadastradas. Impossível cadastrar um produto", category='danger')
        return redirect(url_for('produto.lista'))

    form = NovoProdutoForm()
    form.categoria.choices = Categoria.get_tuples_id_atributo()
    if not form.categoria.choices:
        current_app.logger.fatal(f"Problema na criação das tuplas de categoria")
        abort(500)

    if form.validate_on_submit():
        categoria = Categoria.get_by_id(form.categoria.data)
        if categoria is None:
            flash("Categoria inválida", category='info')
            return redirect(url_for('produto.lista'))

        produto = Produto()
        produto.nome = form.nome.data
        produto.preco = form.preco.data
        produto.ativo = form.ativo.data
        produto.categoria = categoria
        if form.foto_raw.data:
            produto.possui_foto = True
            produto.foto_base64 = b64encode(request.files[form.foto_raw.name].read()).decode('ascii')
            produto.foto_mime = request.files[form.foto_raw.name].mimetype
        else:
            produto.possui_foto = False
            produto.foto_base64 = None
            produto.foto_mime = None
        db.session.add(produto)
        db.session.commit()
        flash(message=f"Produto \"{form.nome.data}\" adicionado", category='success')
        return redirect(url_for('produto.lista'))
    return render_template('render_simple_form.jinja',
                           title="Novo produto",
                           form=form)


@bp.route('/edit/<uuid:id_produto>', methods=['GET', 'POST'])
@login_required
@papeis_aceitos('Admin')
def edit(id_produto):
    produto = Produto.get_by_id(id_produto)
    if produto is None:
        return redirect(url_for('produto.lista'))

    form = EditProdutoForm()
    form.categoria.default = str(produto.categoria.id)
    form.categoria.choices = Categoria.get_tuples_id_atributo()

    if form.validate_on_submit():
        categoria = Categoria.get_by_id(form.categoria.data)
        if categoria is None:
            flash("Categoria inválida", category='info')
            return redirect(url_for('produto.lista'))

        produto.nome = form.nome.data
        produto.preco = form.preco.data
        produto.ativo = form.ativo.data
        produto.categoria = categoria
        if form.remover_imagem.data:
            produto.possui_foto = False
            produto.foto_base64 = None
            produto.foto_mime = None
        elif form.foto_raw.data:
            produto.possui_foto = True
            produto.foto_base64 = b64encode(request.files[form.foto_raw.name].read()).decode('ascii')
            produto.foto_mime = request.files[form.foto_raw.name].mimetype
        db.session.commit()
        flash(message="Produto alterado!", category='success')
        return redirect(url_for('produto.lista'))

    form.categoria.default = str(produto.categoria.id)
    form.categoria.choices = Categoria.get_tuples_id_atributo()
    form.process()
    form.nome.data = produto.nome
    form.preco.data = produto.preco
    form.ativo.data = produto.ativo

    return render_template('produto/edit.jinja',
                           form=form,
                           produto=produto,
                           title="Alterar produto")


@bp.route('/remove/<uuid:id_produto>', methods=['GET', 'POST'])
@login_required
@papeis_aceitos('Admin')
def remove(id_produto):
    produto = Produto.get_by_id(id_produto)
    if produto is None:
        return redirect(url_for('produto.lista'))

    if request.method == 'POST':  # confirmação da remoção
        db.session.delete(produto)
        db.session.commit()
        flash(message="Produto removido!", category='success')
        return redirect(url_for('produto.lista'))

    return render_template('produto/remove.jinja',
                           produto=produto,
                           title="Remover produto")


@bp.route('/<uuid:id_produto>/imagem', methods=['GET'])
@login_required
def imagem(id_produto):
    produto = Produto.get_by_id(id_produto)
    if produto is None:
        return Response(status=404)
    imagem_content, imagem_type = produto.imagem
    return Response(imagem_content, mimetype=imagem_type)


@bp.route('/<uuid:id_produto>/thumbnail', methods=['GET'])
@bp.route('/<uuid:id_produto>/thumbnail/<int:max_size>', methods=['GET'])
@login_required
def thumbnail(id_produto, max_size: int = 64):
    produto = Produto.get_by_id(id_produto)
    if produto is None:
        return Response(status=404)
    imagem_content, imagem_type = produto.thumbnail(max_size=max_size)
    return Response(imagem_content, mimetype=imagem_type)


@bp.route('/em_falta', methods=['GET'])
@login_required
def emfalta():
    pdf = True if request.args.get('pdf') else False
    sentenca = db.select(Produto).where(Produto.estoque <= 0).order_by(Produto.estoque.asc())
    rset = db.session.execute(sentenca).scalars()
    if not rset:
        flash("Não há produtos em falta", category="success")
        return redirect(url_for('produto.lista'))
    if pdf:
        return render_template('produto/emfalta.jinja',
                               title="Produtos em falta",
                               rset=rset)
    else:
        return render_template('produto/emfalta.jinja',
                               title="Produtos em falta",
                               rset=rset)
