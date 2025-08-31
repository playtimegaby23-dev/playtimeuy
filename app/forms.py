# app/forms.py
# =========================================================
# Formularios de PlayTimeUY
# Usamos Flask-WTF con validaciones modernas
# =========================================================

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField,
    BooleanField, DateField, SelectField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo,
    ValidationError
)
import datetime


# =========================================================
# Formulario de Registro
# =========================================================
class RegisterForm(FlaskForm):
    username = StringField(
        "Nombre de usuario",
        validators=[
            DataRequired(message="El nombre de usuario es obligatorio."),
            Length(min=3, max=20, message="Debe tener entre 3 y 20 caracteres.")
        ]
    )

    email = StringField(
        "Correo electrónico",
        validators=[
            DataRequired(message="El correo es obligatorio."),
            Email(message="Correo inválido.")
        ]
    )

    password = PasswordField(
        "Contraseña",
        validators=[
            DataRequired(message="La contraseña es obligatoria."),
            Length(min=6, message="Debe tener al menos 6 caracteres.")
        ]
    )

    confirm_password = PasswordField(
        "Confirmar contraseña",
        validators=[
            DataRequired(message="Debes confirmar tu contraseña."),
            EqualTo("password", message="Las contraseñas no coinciden.")
        ]
    )

    dob = DateField(
        "Fecha de nacimiento",
        format="%Y-%m-%d",
        validators=[DataRequired(message="La fecha de nacimiento es obligatoria.")]
    )

    country = StringField(
        "País",
        validators=[
            DataRequired(message="El país es obligatorio."),
            Length(max=50, message="Máximo 50 caracteres.")
        ]
    )

    role = SelectField(
        "Rol",
        choices=[
            ("usuario", "Usuario"),
            ("promotor", "Promotor"),
            ("modelo", "Modelo/Artista")
        ],
        validators=[DataRequired(message="Selecciona un rol.")]
    )

    terms = BooleanField(
        "Acepto los Términos y Condiciones",
        validators=[DataRequired(message="Debes aceptar los términos.")]
    )

    submit = SubmitField("Registrarme")

    # ------------------- Validadores personalizados -------------------
    def validate_dob(self, field):
        hoy = datetime.date.today()
        edad = hoy.year - field.data.year - (
            (hoy.month, hoy.day) < (field.data.month, field.data.day)
        )
        if edad < 18:
            raise ValidationError("Debes tener al menos 18 años para registrarte.")

    def validate_username(self, field):
        # 🚨 Ejemplo: podés integrar con Firebase o BD más adelante
        prohibidos = ["admin", "root", "soporte"]
        if field.data.lower() in prohibidos:
            raise ValidationError("Ese nombre de usuario no está permitido.")
