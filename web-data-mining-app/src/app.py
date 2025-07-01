from flask import Flask, render_template
from routes.search_routes import search_bp
from routes.clients_routes import clients_bp
from routes.auto_search_routes import auto_search_bp
from routes.followup_routes import followup_bp
from models.database import db
from config import Config
from routes.auth_routes import auth_bp, google_bp
from routes.crm_routes import crm_bp
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar la base de datos
db.init_app(app)
migrate = Migrate(app, db)

# Registrar blueprints
app.register_blueprint(search_bp)
app.register_blueprint(clients_bp)
app.register_blueprint(auto_search_bp)
app.register_blueprint(followup_bp)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(google_bp, url_prefix='/auth/google')
app.register_blueprint(crm_bp)

# Función para limpiar texto de caracteres mal codificados
def clean_text_filter(text):
    """Filtro de Jinja2 para limpiar texto de caracteres mal codificados"""
    if not text:
        return text
    
    import html
    import unicodedata
    import re
    
    # Corregir caracteres mal codificados comunes
    replacements = {
        'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
        'Ã±': 'ñ', 'Ã¼': 'ü', 'Ã ': 'à', 'Ã¨': 'è', 'Ã¬': 'ì',
        'Ã²': 'ò', 'Ã¹': 'ù', 'Ã§': 'ç', 'Ã„': 'Ä', 'Ã–': 'Ö',
        'Ã': 'Ñ', 'â€™': "'", 'â€œ': '"', 'â€': '"', 'â€¦': '...',
        'â‚¬': '€', 'Â°': '°', 'Â': '', 'â€"': '-', 'â€™': "'",
        'Ã¢': 'â', 'Ã´': 'ô', 'Ã®': 'î', 'Ã«': 'ë', 'Ã¿': 'ÿ',
        # Símbolos problemáticos
        '©': '', '®': '', '™': '', '℠': '',  # Marcas registradas
        'â': '', '€': '', '¢': '', '£': '', '¥': '',  # Monedas problemáticas
        'º': '°', 'ª': '', '°': '°',  # Ordinales
        '–': '-', '—': '-', ''': "'", ''': "'", '"': '"', '"': '"',  # Guiones y comillas
        '…': '...', '•': '-', '·': '-',  # Puntos y viñetas
    }
    
    # Aplicar correcciones
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    
    # Decodificar entidades HTML
    text = html.unescape(text)
    
    # Normalizar unicode (NFD -> NFC)
    text = unicodedata.normalize('NFC', text)
    
    # Limpiar espacios extras y caracteres de control
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)
    
    return text

# Función para verificar si una fecha está vencida
def is_overdue_filter(fecha):
    """Filtro de Jinja2 para verificar si una fecha está vencida manejando None"""
    if not fecha:
        return False
    
    try:
        from datetime import datetime
        # Manejar tanto datetime como date
        if hasattr(fecha, 'date'):
            fecha_comparar = fecha.date() if hasattr(fecha, 'date') else fecha
            return fecha_comparar < datetime.now().date()
        else:
            return fecha < datetime.now()
    except (TypeError, AttributeError) as e:
        print(f"Error en is_overdue_filter: {e}, fecha: {fecha}, tipo: {type(fecha)}")
        return False

# Función para ordenar tareas de forma segura
def sort_tasks_filter(tareas):
    """Filtro de Jinja2 para ordenar tareas por fecha de vencimiento manejando None"""
    def sort_key(task):
        try:
            # Si no hay fecha de vencimiento, poner al final
            if not task.fecha_vencimiento:
                return (1, task.id if hasattr(task, 'id') else 0)  # Usar ID como criterio secundario
            # Si hay fecha, poner al principio ordenado por fecha
            # Convertir fecha a timestamp para evitar comparaciones problemáticas
            if hasattr(task.fecha_vencimiento, 'timestamp'):
                return (0, task.fecha_vencimiento.timestamp())
            else:
                return (0, task.fecha_vencimiento)
        except (AttributeError, TypeError) as e:
            print(f"Error en sort_tasks_filter: {e}, tarea: {task}")
            # En caso de error, poner al final
            return (1, getattr(task, 'id', 0))
    
    try:
        return sorted(tareas, key=sort_key)
    except Exception as e:
        print(f"Error general en sort_tasks_filter: {e}")
        # En caso de error, devolver la lista sin ordenar
        return list(tareas)

# Registrar los filtros de Jinja2
app.jinja_env.filters['clean_text'] = clean_text_filter
app.jinja_env.filters['is_overdue'] = is_overdue_filter
app.jinja_env.filters['sort_tasks'] = sort_tasks_filter

# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')

# Crear las tablas de la base de datos
with app.app_context():
    try:
        db.create_all()
        print("✅ Base de datos inicializada correctamente")
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")
        print("Asegúrate de que PostgreSQL esté corriendo y la base de datos 'mining_db' exista")

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)