from flask import Blueprint, render_template, request, redirect, url_for, flash

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Acá procesás los datos del formulario
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validación simple
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'error')
            return redirect(url_for('main.register'))

        # Aquí iría la lógica de guardado en base de datos

        flash('Registro exitoso. ¡Iniciá sesión!')
        return redirect(url_for('main.login'))

    return render_template('register.html')

@main.route('/login')
def login():
    return render_template('login.html')
