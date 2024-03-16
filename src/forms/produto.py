import uuid

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms.fields import SubmitField, StringField, DecimalField, BooleanField, SelectField, FileField
from wtforms.validators import DataRequired, NumberRange, InputRequired, AnyOf


class NovoProdutoForm(FlaskForm):
    nome = StringField("Nome do produto",
                       validators=[DataRequired(message="É obrigatório informar um nome para o produto")])
    preco = DecimalField("Preço do produto", places=2,
                         validators=[NumberRange(min=0, message="O preço deve ser, obrigatoriamente, positivo")])
    categoria = SelectField("Categoria", coerce=uuid.UUID,
                            validators=[InputRequired(message="É necessário escolher uma categoria "
                                                              "válida para o produto")])
    foto_raw = FileField("Foto do produto",
                         validators=[FileAllowed(['jpg', 'png'],
                                                 message="Apenas arquivos JPG ou PNG")])
    ativo = BooleanField("Produto ativo?", default=True, validators=[AnyOf([True, False])])
    submit = SubmitField("Adicionar")


class EditProdutoForm(FlaskForm):
    nome = StringField("Nome do produto",
                       validators=[DataRequired(message="É obrigatório informar um nome para o produto")])
    preco = DecimalField("Preço do produto", places=2,
                         validators=[NumberRange(min=0, message="O preço deve ser, obrigatoriamente, positivo")])
    categoria = SelectField("Categoria",  # coerce=uuid.UUID,
                            validators=[InputRequired(message="É necessário escolher uma categoria "
                                                              "válida para o produto")])
    foto_raw = FileField("Foto do produto",
                         validators=[FileAllowed(['jpg', 'png'],
                                                 message="Apenas arquivos JPG ou PNG")])
    ativo = BooleanField("Produto ativo?", default=True, validators=[AnyOf([True, False])])
    remover_imagem = BooleanField("Remover imagem?", default=False, validators=[AnyOf([True, False])])
    submit = SubmitField("Alterar")
