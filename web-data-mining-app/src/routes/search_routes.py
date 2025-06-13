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
    search_model = SearchModel(data_mining_service)
    results = search_model.process_search_query(criteria)
    
    # Convertir los campos al español para el frontend
    results_es = []
    for r in results:
        results_es.append({
            'nombre': r.get('name', 'No disponible'),
            'correo': r.get('email', 'No disponible'),
            'telefono': r.get('phone', 'No disponible'),
            'ubicacion': r.get('location', 'No disponible'),
            'pagina_web': r.get('link', 'No disponible')
        })
    
    return jsonify(results_es)