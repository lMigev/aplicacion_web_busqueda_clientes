import time
from collections import Counter
from models.database import db, SearchHistory
from services.data_mining_service import DataMiningService
from flask import Flask
from config import Config
import re

# --- Configuración Flask para acceso a modelos ---
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# --- Utilidad para extraer palabras clave de búsquedas exitosas ---
def get_top_keywords(n=10, min_quality=60):
    with app.app_context():
        # Buscar los criterios de búsqueda que generaron contactos de alta calidad
        from models.database import Contact
        contacts = Contact.query.filter(Contact.quality_score >= min_quality).all()
        all_queries = [c.search_query for c in contacts if c.search_query]
        # Tokenizar y contar palabras clave
        words = []
        for q in all_queries:
            # Eliminar signos de puntuación y minúsculas
            tokens = re.findall(r'\b\w+\b', q.lower())
            words.extend(tokens)
        counter = Counter(words)
        # Excluir palabras muy genéricas
        stopwords = set(['en', 'de', 'la', 'el', 'y', 'para', 'con', 'los', 'las', 'del', 'por', 'a', 'un', 'una'])
        keywords = [w for w, _ in counter.most_common() if w not in stopwords]
        return keywords[:n]

# --- Generar nuevas combinaciones de búsqueda ---
def generate_new_searches(keywords, n=5):
    # Simple: combina las palabras clave más frecuentes en frases
    searches = set()
    for i in range(len(keywords)):
        for j in range(i+1, len(keywords)):
            searches.add(f"{keywords[i]} {keywords[j]} Panamá")
            if len(searches) >= n:
                return list(searches)
    return list(searches)

# --- Ejecutar búsquedas automáticas ---
def run_auto_search():
    with app.app_context():
        print("[AutoSearch] Analizando palabras clave exitosas...")
        keywords = get_top_keywords()
        print(f"[AutoSearch] Palabras clave más frecuentes: {keywords}")
        new_searches = generate_new_searches(keywords)
        print(f"[AutoSearch] Nuevos criterios de búsqueda generados: {new_searches}")
        dms = DataMiningService()
        for criteria in new_searches:
            print(f"[AutoSearch] Ejecutando búsqueda automática: {criteria}")
            dms.search_contacts(criteria)
            time.sleep(2)  # Espera para evitar bloqueos
        print("[AutoSearch] Búsquedas automáticas completadas.")

if __name__ == "__main__":
    run_auto_search()
