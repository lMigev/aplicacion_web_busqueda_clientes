from flask import Blueprint, request, jsonify, render_template
from models.search_model import SearchModel
from services.data_mining_service import DataMiningService

search_bp = Blueprint('search_bp', __name__)

@search_bp.route('/', methods=['GET'])
def menu():
    return render_template('index.html')

@search_bp.route('/busqueda', methods=['GET'])
def busqueda():
    return render_template('busqueda.html')

@search_bp.route('/api/search', methods=['GET'])
def search():
    criteria = request.args.get('criteria', '')
    if not criteria:
        return jsonify([])
    
    data_mining_service = DataMiningService()
    # Buscar contactos pero NO guardar en la base de datos aún
    results = data_mining_service.search_contacts(criteria, save_to_db=False)
    
    from models.database import Contact, db
    existing_contacts = Contact.query.all()
    
    def is_duplicate(contact, existing_contacts):
        for existing in existing_contacts:
            if (contact.get('email') and existing.email and contact['email'].lower() == existing.email.lower()):
                return True
            if (contact.get('phone') and existing.phone and contact['phone'] == existing.phone):
                return True
            if (contact.get('link') and existing.website and contact['link'] == existing.website):
                return True
        return False
    
    nuevos = [r for r in results if not is_duplicate(r, existing_contacts)]
    results_es = []
    if not nuevos:
        return jsonify({'mensaje': 'No se encontraron nuevos resultados. Ya tienes todos los contactos posibles para este criterio.', 'resultados': []})
    
    # Guardar los nuevos en la base de datos después de mostrar
    for r in nuevos:
        new_contact = Contact(
            name=r.get('name', 'Sin nombre'),
            email=r.get('email'),
            phone=r.get('phone'),
            location=r.get('location'),
            website=r.get('link') or r.get('website'),
            search_query=criteria,
            source=r.get('source'),
            quality_score=r.get('quality_score', 0),
            email_valid=r.get('email_valid', False),
            phone_valid=r.get('phone_valid', False)
        )
        try:
            db.session.add(new_contact)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
    
    for r in nuevos:
        results_es.append({
            'nombre': r.get('name', 'No disponible'),
            'correo': r.get('email', 'No disponible'),
            'telefono': r.get('phone', 'No disponible'),
            'ubicacion': r.get('location', 'No disponible'),
            'pagina_web': r.get('link') or r.get('website', 'No disponible')
        })
    return jsonify({'mensaje': '', 'resultados': results_es})