import re

from flask import current_app
from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import Email, InputRequired, EqualTo, ValidationError, Length


# noinspection PyMethodMayBeStatic
class ValidaSenha:
    def validate_password(self, password):
        # Definir a complexidade da senha na forma de expressões regulares
        expressoes = []
        min = current_app.config.get("PASSWORD_MIN", 8)
        max = current_app.config.get("PASSWORD_MAX", 64)
        expressoes.append(f"^(?=.{{{min},{max}}}$)")
        mensagem = f"A sua senha precisa ter entre {min} e {max} caracteres"

        upper = r"(?=.*[A-Z])"  # Pelo menos 1 letra maiúscula
        lower = r"(?=.*[a-z])"  # Pelo menos 1 letra minúscula
        number = r"(?=.*[0-9])"  # Pelo menos um número
        special = r"(?=.*[!@#\$%\&'\(\)*\+,\-./:;<=>?@\[\\\]^_`{|}~])"  # Pelo menos um caracter especial

        if current_app.config.get("PASSWORD_MAIUSCULA", False):
            expressoes.append(upper)
            mensagem = mensagem + ", letras maiúsculas"
        if current_app.config.get("PASSWORD_MINUSCULA", False):
            expressoes.append(lower)
            mensagem = mensagem + ", letras minúsculas"
        if current_app.config.get("PASSWORD_NUMERO", False):
            expressoes.append(number)
            mensagem = mensagem + ", números"
        if current_app.config.get("PASSWORD_SIMBOLO", False):
            expressoes.append(special)
            mensagem = mensagem + ", símbolos especiais"

        pattern = "".join(expressoes)

        # Troca a última ocorrência de vírgula, se houver, por ' e '
        pos = mensagem.rfind(', ')
        if pos > -1: mensagem = mensagem[:pos] + ' e ' + mensagem[pos + 2:]

        if not re.match(pattern, str(password.data)):
            raise ValidationError(mensagem)


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
    submit = SubmitField("Redefinir a senha")


class SetNewPasswordForm(FlaskForm, ValidaSenha):
    password = PasswordField("Nova senha",
                             validators=[InputRequired(message="É necessário escolher uma senha")])
    password2 = PasswordField("Confirme a nova senha",
                              validators=[InputRequired(message="É necessário repetir a senha"),
                                          EqualTo("password", message="As senhas não são iguais")])
    submit = SubmitField("Cadastrar a nova senha")


# noinspection PyMethodMayBeStatic
class RegistrationForm(FlaskForm, ValidaSenha):
    nome = StringField("Nome",
                       validators=[InputRequired(message="É obrigatório informar o nome para cadastro")])
    email = StringField("Email",
                        validators=[InputRequired(message="É obrigatório informar o email do cadastro"),
                                    Email(message="Informe um email válido", check_deliverability=True)])

    password = PasswordField("Senha",
                             validators=[InputRequired(message="É necessário escolher uma senha")])
    password2 = PasswordField("Confirme a senha",
                              validators=[InputRequired(message="É necessário repetir a senha"),
                                          EqualTo('password', message="As senhas não são iguais")])
    submit = SubmitField("Adicionar usuário")

    def validate_email(self, email):
        from src.models.usuario import User
        user = User.get_by_email(email.data)
        if user:
            raise ValidationError("Este email já está cadastrado")


class ProfileForm(FlaskForm):
    nome = StringField("Nome",
                       validators=[InputRequired(message="É obrigatório informar o nome para cadastro")])
    usa_2fa = BooleanField("Ativar autenticação em dois fatores")
    submit = SubmitField("Efetuar mudanças")


class Read2FACodeForm(FlaskForm):
    # https://web.dev/articles/sms-otp-form
    codigo = StringField("Código",
                         validators=[InputRequired(message="Informe o código fornecido pelo aplicativo "
                                                           "autenticador, ou um dos códigos reserva"),
                                     Length(min=6, max=6)],
                         render_kw={'inputmode': 'numeric',
                                    'autocomplete': 'one-time-code',
                                    'pattern': r'\d{6}'})
    submit = SubmitField("Enviar código")
