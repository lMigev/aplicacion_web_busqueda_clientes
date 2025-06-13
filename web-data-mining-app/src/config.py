import os

class Config:
    # Configuración de PostgreSQL - Ajusta estos valores según tu instalación
    # Formato: postgresql://usuario:contraseña@host:puerto/nombre_base_datos
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'postgresql://postgres:Pastorcitos05@localhost:5432/mining_db?client_encoding=utf8'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'client_encoding': 'utf8'
        }
    }
    
    # Otras configuraciones
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
