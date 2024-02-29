from flask_wtf import FlaskForm
from wtforms.fields.simple import SubmitField, StringField
from wtforms.validators import DataRequired


class NovoCategoriaForm(FlaskForm):
    nome = StringField("Nome da categoria",
                       validators=[DataRequired(message="É obrigatório informar um nome para a categoria")])
    submit = SubmitField("Adicionar")
