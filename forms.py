from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from database import get_db


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')


class RegistrationForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[
        DataRequired(), 
        Length(min=3, max=80, message='Nome deve ter entre 3 e 80 caracteres')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[
        DataRequired(),
        Length(min=6, message='Senha deve ter no mínimo 6 caracteres')
    ])
    password2 = PasswordField('Confirmar Senha', validators=[
        DataRequired(), 
        EqualTo('password', message='As senhas devem ser iguais')
    ])
    submit = SubmitField('Criar Conta')
    
    def validate_username(self, username):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username.data,))
        user = cursor.fetchone()
        conn.close()
        if user:
            raise ValidationError('Este nome de usuário já está em uso.')
    
    def validate_email(self, email):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ?', (email.data,))
        user = cursor.fetchone()
        conn.close()
        if user:
            raise ValidationError('Este email já está cadastrado.'rado.')
