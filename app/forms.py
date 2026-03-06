# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, TextAreaField, FileField, MultipleFileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from .models import User

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[
        DataRequired(message='El usuario es obligatorio'),
        Length(min=3, max=80, message='El usuario debe tener entre 3 y 80 caracteres')
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es obligatoria')
    ])
    remember = BooleanField('Recordarme')

class RegistrationForm(FlaskForm):
    username = StringField('Usuario', validators=[
        DataRequired(), 
        Length(min=3, max=80)
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Email(message='Email inválido')
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(), 
        Length(min=8, message='La contraseña debe tener al menos 8 caracteres')
    ])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(), 
        EqualTo('password', message='Las contraseñas no coinciden')
    ])
    role = SelectField('Rol', choices=[
        ('viewer', 'Espectador (solo ver)'),
        ('editor', 'Editor (ver y subir)')
    ])
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nombre de usuario ya está registrado.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este email ya está registrado.')

class UserEditForm(FlaskForm):
    username = StringField('Usuario', validators=[
        DataRequired(), 
        Length(min=3, max=80)
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Email()
    ])
    role = SelectField('Rol', choices=[
        ('viewer', 'Espectador'),
        ('editor', 'Editor'),
        ('admin', 'Administrador')
    ])
    is_active = BooleanField('Usuario Activo')
    new_password = PasswordField('Nueva Contraseña', validators=[
        Optional(),
        Length(min=8, message='La contraseña debe tener al menos 8 caracteres')
    ])
    confirm_new_password = PasswordField('Confirmar Nueva Contraseña', validators=[
        Optional(),
        EqualTo('new_password', message='Las contraseñas no coinciden')
    ])

class FolderForm(FlaskForm):
    name = StringField('Nombre de la carpeta', validators=[
        DataRequired(), 
        Length(min=3, max=100)
    ])
    path = StringField('Ruta en el sistema', validators=[
        DataRequired(),
        Length(min=3, max=500)
    ])
    description = TextAreaField('Descripción', validators=[Optional()])
    allowed_roles = StringField('Roles permitidos', validators=[Optional()], 
                               default='viewer,editor,admin')
    is_active = BooleanField('Activa', default=True)

class UploadForm(FlaskForm):
    files = MultipleFileField('Archivos', validators=[DataRequired()])
    folder_id = SelectField('Carpeta destino', coerce=int, validators=[DataRequired()])

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Contraseña actual', validators=[DataRequired()])
    new_password = PasswordField('Nueva contraseña', validators=[
        DataRequired(),
        Length(min=8, message='La contraseña debe tener al menos 8 caracteres')
    ])
    confirm_new_password = PasswordField('Confirmar nueva contraseña', validators=[
        DataRequired(),
        EqualTo('new_password', message='Las contraseñas no coinciden')
    ])

class ProfileForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])