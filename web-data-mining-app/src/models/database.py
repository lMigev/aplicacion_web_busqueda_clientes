from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Index
import html
import unicodedata
import re

db = SQLAlchemy()

class Contact(db.Model):
    __tablename__ = 'contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    website = db.Column(db.String(500), nullable=True)
    
    # Metadatos para análisis
    search_query = db.Column(db.String(200), nullable=False)  # Qué búsqueda lo encontró
    source = db.Column(db.String(50), nullable=False)  # 'google' o 'duckduckgo'
    quality_score = db.Column(db.Float, default=0.0)  # Puntuación de calidad (0-100)
    
    # Validación de datos
    email_valid = db.Column(db.Boolean, default=False)
    phone_valid = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índices para optimizar búsquedas
    __table_args__ = (        Index('idx_email', 'email'),
        Index('idx_phone', 'phone'),
        Index('idx_website', 'website'),
        Index('idx_search_query', 'search_query'),
        Index('idx_quality_score', 'quality_score'),
    )
    
    def __repr__(self):
        return f'<Contact {self.name}>'
    
    @staticmethod
    def clean_text(text):
        """Limpia y corrige problemas de codificación en el texto"""
        if not text:
            return text
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
    
    # Eliminar campos tags y notes, ya que ahora se usan followups
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.clean_text(self.name),
            'email': self.email,
            'phone': self.phone,
            'location': self.clean_text(self.location),
            'website': self.website,
            'search_query': self.search_query,
            'source': self.source,
            'quality_score': self.quality_score,
            'email_valid': self.email_valid,
            'phone_valid': self.phone_valid,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SearchHistory(db.Model):
    __tablename__ = 'search_history'
    
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String(200), nullable=False)
    results_found = db.Column(db.Integer, default=0)
    search_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SearchHistory {self.query}>'

class FollowUp(db.Model):
    __tablename__ = 'followups'
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False)
    tag = db.Column(db.String(100), nullable=True)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    contact = db.relationship('Contact', backref=db.backref('followups', lazy=True))

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')  # user o admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Opportunity(db.Model):
    __tablename__ = 'opportunities'
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False)
    estado = db.Column(db.String(32), default='Nuevo')  # Nuevo, En seguimiento, Oportunidad, Cerrado
    nota = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_ultimo_contacto = db.Column(db.DateTime)
    valor_estimado = db.Column(db.Float, default=0.0)  # Valor estimado de la oportunidad
    probabilidad = db.Column(db.Integer, default=25)  # Probabilidad de cierre (0-100)
    fecha_cierre_estimada = db.Column(db.Date)  # Fecha estimada de cierre
    prioridad = db.Column(db.String(16), default='Media')  # Alta, Media, Baja
    canal_origen = db.Column(db.String(64))  # Canal de origen del lead
    representante = db.Column(db.String(128))  # Representante asignado
    ultima_actividad = db.Column(db.DateTime, default=datetime.utcnow)
    
    contact = db.relationship('Contact', backref=db.backref('opportunities', lazy=True))
    tareas = db.relationship('Task', backref='opportunity', lazy=True, cascade='all, delete-orphan')
    actividades = db.relationship('Activity', backref='opportunity', lazy=True, cascade='all, delete-orphan')

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'), nullable=False)
    asignado_a_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Usuario asignado
    descripcion = db.Column(db.String(256))
    completada = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_vencimiento = db.Column(db.DateTime)  # Fecha límite para completar
    prioridad = db.Column(db.String(16), default='Media')  # Alta, Media, Baja
    tipo = db.Column(db.String(32), default='General')  # Llamada, Email, Reunión, etc.
    resultado = db.Column(db.Text)  # Resultado o comentarios de la tarea
    fecha_completada = db.Column(db.DateTime)  # Cuándo se completó
    
    # Relaciones
    asignado_a = db.relationship('User', backref=db.backref('tareas_asignadas', lazy=True))

class Activity(db.Model):
    __tablename__ = 'activities'
    id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'), nullable=False)
    tipo = db.Column(db.String(32), nullable=False)  # llamada, email, nota, cambio_estado, etc.
    descripcion = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.Column(db.String(128))  # Quién realizó la actividad
    detalles = db.Column(db.JSON)  # Información adicional en formato JSON
