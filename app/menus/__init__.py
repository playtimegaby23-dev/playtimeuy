
from flask import Blueprint

# Crear Blueprint para los menús
menus = Blueprint('menus', __name__, template_folder='templates', static_folder='static')

# Aquí puedes importar las rutas del menú
from . import routes  # Importa las rutas dentro de app/menus/routes.py
