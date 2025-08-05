from flask import render_template, session, redirect, url_for
from app.menus import menus
from firebase_admin import firestore

db = firestore.client()

@menus.route('/menu')
def mostrar_menu():
    """
    Ruta de ejemplo para mostrar un menú dinámico basado en el tipo de cuenta del usuario.
    """
    if 'user' not in session:
        return redirect(url_for('main.login'))

    user_info = session['user']
    user_email = user_info.get('email')
    user_type = user_info.get('type', '')  # 'creadora', 'comprador', 'admin', etc.

    # Opcional: Cargar más información desde Firestore si querés
    try:
        user_doc = db.collection('usuarios').document(user_email).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
        else:
            user_data = {}
    except Exception as e:
        user_data = {}
        print(f"Error al cargar datos del usuario: {e}")

    return render_template('menus/menu.html', user_type=user_type, user_data=user_data)
