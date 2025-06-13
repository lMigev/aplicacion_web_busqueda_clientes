from flask import Flask
from routes.search_routes import search_bp
from routes.clients_routes import clients_bp
from routes.auto_search_routes import auto_search_bp
from routes.followup_routes import followup_bp
from models.database import db
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar la base de datos
db.init_app(app)

# Registrar blueprints
app.register_blueprint(search_bp)
app.register_blueprint(clients_bp)
app.register_blueprint(auto_search_bp)
app.register_blueprint(followup_bp)

# Crear las tablas de la base de datos
with app.app_context():
    try:
        db.create_all()
        print("✅ Base de datos inicializada correctamente")
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")
        print("Asegúrate de que PostgreSQL esté corriendo y la base de datos 'mining_db' exista")

if __name__ == '__main__':
    app.run(debug=True)