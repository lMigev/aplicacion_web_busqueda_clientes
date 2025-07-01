from flask import Blueprint, request, jsonify, redirect, url_for, session, render_template
from flask_dance.contrib.google import make_google_blueprint, google
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import db, User
import jwt
import datetime
import os

# Configuración JWT
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'supersecretkey')

auth_bp = Blueprint('auth_bp', __name__)

google_bp = make_google_blueprint(
    client_id=os.environ.get('GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_ID_AQUI'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET', 'GOOGLE_CLIENT_SECRET_AQUI'),
    scope=["profile", "email"],
    redirect_url="/auth/google/callback"
)

# Registro clásico
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'msg': 'Faltan datos'}), 400
    if User.query.filter((User.username==data['username']) | (User.email==data['email'])).first():
        return jsonify({'msg': 'Usuario o email ya existe'}), 409
    # Si no hay usuarios, el primero será admin
    is_first_user = User.query.count() == 0
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role='admin' if is_first_user else 'user'
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'msg': f"Usuario registrado como {'admin' if is_first_user else 'user'}"}), 201

# Login clásico
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()
    if not user or not check_password_hash(user.password_hash, data.get('password')):
        return jsonify({'msg': 'Credenciales inválidas'}), 401
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=12)
    }, SECRET_KEY, algorithm='HS256')
    return jsonify({'token': token, 'user': user.to_dict()})

# Login con Google
@auth_bp.route('/login/google')
def login_google():
    return redirect(url_for('google.login'))

@auth_bp.route('/google/callback')
def google_callback():
    if not google.authorized:
        return redirect(url_for('auth_bp.login_google'))
    resp = google.get('/oauth2/v2/userinfo')
    if not resp.ok:
        return jsonify({'msg': 'Error autenticando con Google'}), 400
    info = resp.json()
    user = User.query.filter_by(email=info['email']).first()
    if not user:
        user = User(
            username=info['email'].split('@')[0],
            email=info['email'],
            password_hash=generate_password_hash(os.urandom(16).hex()),
            role='user'
        )
        db.session.add(user)
        db.session.commit()
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=12)
    }, SECRET_KEY, algorithm='HS256')
    # Aquí puedes redirigir a frontend con el token como parámetro o cookie
    return jsonify({'token': token, 'user': user.to_dict()})

@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

# Ruta temporal para crear un usuario vendedor1 para pruebas
@auth_bp.route('/create-test-user')
def create_test_user():
    """Crea un usuario de prueba 'vendedor1' para pruebas de mis-tareas"""
    # Verificar si ya existe
    user = User.query.filter_by(username='vendedor1').first()
    if user:
        return jsonify({
            "success": True,
            "message": "El usuario vendedor1 ya existe",
            "user": user.to_dict()
        })
    
    # Crear el usuario
    new_user = User(
        username='vendedor1',
        email='vendedor1@example.com',
        password_hash=generate_password_hash('password123'),
        role='user'
    )
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Usuario vendedor1 creado correctamente",
        "user": new_user.to_dict()
    })
