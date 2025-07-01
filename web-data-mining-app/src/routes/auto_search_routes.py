from flask import Blueprint, jsonify, request, render_template
from collections import Counter
from models.database import db, Contact
import re
from services.data_mining_service import DataMiningService

auto_search_bp = Blueprint('auto_search_bp', __name__)

# Utilidad para extraer palabras clave de búsquedas exitosas
def get_top_keywords(n=10, min_quality=60):
    contacts = Contact.query.filter(Contact.quality_score >= min_quality).all()
    all_queries = [c.search_query for c in contacts if c.search_query]
    words = []
    for q in all_queries:
        tokens = re.findall(r'\b\w+\b', q.lower())
        words.extend(tokens)
    counter = Counter(words)
    stopwords = set(['en', 'de', 'la', 'el', 'y', 'para', 'con', 'los', 'las', 'del', 'por', 'a', 'un', 'una'])
    keywords = [w for w, _ in counter.most_common() if w not in stopwords]
    return keywords[:n]

def generate_new_searches(keywords, n=10):
    searches = set()
    for i in range(len(keywords)):
        for j in range(i+1, len(keywords)):
            searches.add(f"{keywords[i]} {keywords[j]} Panamá")
            if len(searches) >= n:
                return list(searches)
    return list(searches)

@auto_search_bp.route('/recomendaciones', methods=['GET', 'POST'])
def recomendaciones_page():
    recomendaciones = []
    resultados = []
    
    # Obtener recomendaciones
    try:
        keywords = get_top_keywords()
        recs = generate_new_searches(keywords, n=10)
        recomendaciones = [{'criterio': r, 'motivo': 'Basado en búsquedas exitosas'} for r in recs]
    except Exception as e:
        print(f"Error generando recomendaciones: {e}")
        recomendaciones = []

    # Si la petición es AJAX o tiene ?json=1, devolver JSON
    if request.args.get('json') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'recomendaciones': recomendaciones})

    if request.method == 'POST':
        seleccionadas = request.form.getlist('seleccionadas')
        if seleccionadas:
            print(f"Ejecutando búsquedas para: {seleccionadas}")
            dms = DataMiningService()
            
            # Limitar a máximo 3 búsquedas por vez para evitar sobrecarga
            seleccionadas = seleccionadas[:3]
            
            for i, criterio in enumerate(seleccionadas):
                try:
                    print(f"Procesando búsqueda {i+1}/{len(seleccionadas)}: {criterio}")
                    
                    # Ejecutar búsqueda con límite reducido para evitar timeout
                    contacts = dms.search_contacts_limited(criterio, max_results=5)
                    
                    if contacts:
                        resultados.append(f"✅ Búsqueda '{criterio}': {len(contacts)} contactos encontrados")
                    else:
                        resultados.append(f"⚠️ Búsqueda '{criterio}': Sin resultados")
                        
                except Exception as e:
                    print(f"Error en búsqueda '{criterio}': {e}")
                    resultados.append(f"❌ Error en búsqueda '{criterio}': {str(e)}")
                    continue
        else:
            resultados.append("❌ No se seleccionaron criterios de búsqueda")
    
    return render_template('recomendaciones.html', recomendaciones=recomendaciones, resultados=resultados)

@auto_search_bp.route('/api/recomendaciones', methods=['GET'])
def get_recomendaciones():
    keywords = get_top_keywords()
    recomendaciones = generate_new_searches(keywords, n=10)
    return jsonify(recomendaciones)

@auto_search_bp.route('/api/ejecutar_busquedas', methods=['POST'])
def ejecutar_busquedas():
    data = request.get_json()
    criterios = data.get('criterios', [])
    dms = DataMiningService()
    resultados = []
    for criterio in criterios:
        dms.search_contacts(criterio)
        resultados.append({'criterio': criterio, 'status': 'ok'})
    return jsonify({'resultados': resultados})
