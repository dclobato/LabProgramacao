import re

from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import Email, InputRequired, EqualTo, ValidationError


# noinspection PyMethodMayBeStatic
class ValidaSenha:
    def validate_password(self, password):
        # Definir a complexidade da senha na forma de expressões regulares
        min_max_length = r"^(?=.{8,32}$)"  # 8 a 32 símbolos
        upper = r"(?=.*[A-Z])"  # Pelo menos 1 letra maiúscula
        lower = r"(?=.*[a-z])"  # Pelo menos 1 letra minúscula
        number = r"(?=.*[0-9])"  # Pelo menos um número
        special = r"(?=.*[!@#\$%\&'\(\)*\+,\-./:;<=>?@\[\\\]^_`{|}~])"  # Pelo menos um caracter especial

        # Combina as expressões regulares em uma única expressão
        pattern = min_max_length + upper + lower + number + special

        if not re.match(pattern, str(password.data)):
            raise ValidationError(
                'A sua senha precisa ter entre 8 e 32 caracteres e conter letras maiúsculas,'
                ' minúsculas, números e símbolos especiais')


class LoginForm(FlaskForm):
    email = StringField("Email",
                        validators=[InputRequired(message="É obrigatório informar o email do cadastro"),
                                    Email(message="Informe um email válido", check_deliverability=False)])
    password = PasswordField("Senha",
                             validators=[InputRequired(message="É necessário digitar a senha")])

    remember_me = BooleanField("Permanecer conectado?",
                               default=True)
    submit = SubmitField("Entrar")


class AskToResetPassword(FlaskForm):
    email = StringField("Email",
                        validators=[InputRequired(
                            message="É obrigatório informar o email para o qual se deseja definir nova senha"),
                            Email(message="Informe um email válido", check_deliverability=False)])
    submit = SubmitField('Enviar pedido para redefinição de senha')


class SetNewPasswordForm(FlaskForm, ValidaSenha):
    password = PasswordField('Nova senha',
                             validators=[InputRequired(message="É necessário escolher uma senha")])
    password2 = PasswordField('Confirme a nova senha',
                              validators=[InputRequired(message="É necessário repetir a senha"),
                                          EqualTo('password', message="As senhas não são iguais")])
    submit = SubmitField('Cadastrar a nova senha')
