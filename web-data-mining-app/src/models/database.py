from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Index

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
    __table_args__ = (
        Index('idx_email', 'email'),
        Index('idx_phone', 'phone'),
        Index('idx_website', 'website'),
        Index('idx_search_query', 'search_query'),
        Index('idx_quality_score', 'quality_score'),
    )
    
    def __repr__(self):
        return f'<Contact {self.name}>'
    
    # Eliminar campos tags y notes, ya que ahora se usan followups
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'location': self.location,
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
