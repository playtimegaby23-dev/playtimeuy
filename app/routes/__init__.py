from flask import Blueprint

# Importa los blueprints definidos en este paquete
from .main import main

# Si en el futuro agregás más blueprints, los importás aquí
# Ejemplo:
# from .auth import auth_bp
# from .admin import admin_bp

# Lista de blueprints para registrar fácilmente en la app principal
__all__ = ['main']  # Agregá aquí otros blueprints cuando los crees
