from googlesearch import search
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import re
from models.database import Contact, SearchHistory, db
from services.validator import DataValidator

class DataMiningService:
    def __init__(self):
        pass

    def search_contacts(self, criteria):
        print(f"Iniciando búsqueda para: {criteria}")
        # Dominios a excluir (redes sociales y otros)
        excluded_domains = [
            'facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com', 'youtube.com',
            'tiktok.com', 'wa.me', 'web.whatsapp.com', 'pinterest.com', 'snapchat.com',
            'wikipedia.org', 'maps.google.com', 'goo.gl', 'bit.ly', 'messenger.com',
            'plus.google.com', 'tumblr.com', 'reddit.com', 'telegram.me', 't.me', 'threads.net'
        ]
        # Buscar en motores
        google_results = self.search_google_scrape(criteria)
        duckduckgo_results = self.search_duckduckgo(criteria)
        all_results = google_results + duckduckgo_results
        contacts = []
        new_contacts_count = 0
        existing_contacts = Contact.query.all()
        seen = set()
        scraped_urls = set()
        for i, result in enumerate(all_results):
            url = result.get('link')
            # Filtrar resultados no deseados
            if not url or any(domain in url for domain in excluded_domains):
                print(f"❌ URL excluida por dominio: {url}")
                continue
            if url.startswith('/search?') or url.startswith('https://www.google.com/search?'):
                print(f"❌ URL excluida por ser resultado de Google Search: {url}")
                continue
            # Evitar repetir scraping en la misma búsqueda
            if url in scraped_urls:
                print(f"⚠️ URL ya scrapeada en esta búsqueda: {url}")
                continue
            scraped_urls.add(url)
            print(f"Procesando resultado {i+1}: {url}")
            contact_data = self.scrape_contact_info(url, result.get('name'))
            contact_data['search_query'] = criteria
            contact_data['source'] = result.get('source', 'unknown')
            
            # Validar datos
            email_valid, email_msg = DataValidator.validate_email(contact_data.get('email'))
            phone_valid, phone_msg = DataValidator.validate_phone(contact_data.get('phone'))
            
            contact_data['email_valid'] = email_valid
            contact_data['phone_valid'] = phone_valid
            
            if email_valid:
                contact_data['email'] = email_msg
            if phone_valid:
                contact_data['phone'] = phone_msg
            
            # Calcular puntuación de calidad
            contact_data['quality_score'] = DataValidator.calculate_quality_score(contact_data)
            # --- NUEVO: Clave única para evitar duplicados en la búsqueda ---
            unique_key = (
                (contact_data.get('name') or '').strip().lower(),
                (contact_data.get('email') or '').strip().lower(),
                (contact_data.get('phone') or '').strip(),
                (contact_data.get('website') or '').strip().lower()
            )
            if unique_key in seen:
                print(f"⚠️ Contacto duplicado en la búsqueda omitido: {contact_data.get('name')}")
                continue
            seen.add(unique_key)
            # --- FIN NUEVO ---
            # Verificar duplicados en la base de datos
            is_dup, dup_msg = DataValidator.is_duplicate(contact_data, existing_contacts)
            
            if not is_dup:
                # Guardar en base de datos
                new_contact = Contact(
                    name=contact_data.get('name', 'Sin nombre'),
                    email=contact_data.get('email'),
                    phone=contact_data.get('phone'),
                    location=contact_data.get('location'),
                    website=contact_data.get('website'),
                    search_query=criteria,
                    source=contact_data.get('source'),
                    quality_score=contact_data.get('quality_score', 0),
                    email_valid=email_valid,
                    phone_valid=phone_valid
                )
                
                try:
                    db.session.add(new_contact)
                    db.session.commit()
                    new_contacts_count += 1
                    print(f"✅ Contacto guardado: {contact_data.get('name')}")
                except Exception as e:
                    print(f"❌ Error guardando contacto: {e}")
                    db.session.rollback()
            else:
                print(f"⚠️ Contacto duplicado en base de datos omitido: {dup_msg}")
            
            contacts.append(contact_data)
        
        # Guardar historial de búsqueda
        try:
            search_history = SearchHistory(
                query=criteria,
                results_found=len(contacts)
            )
            db.session.add(search_history)
            db.session.commit()
        except Exception as e:
            print(f"❌ Error guardando historial: {e}")
        
        print(f"Total de contactos encontrados: {len(contacts)}")
        print(f"Contactos nuevos guardados: {new_contacts_count}")
        return contacts

    def search_google_scrape(self, criteria):
        contacts = []
        try:
            for url in search(criteria, num_results=3, lang="es"):
                contacts.append({
                    "name": f"Resultado de Google: {url[:50]}...",
                    "link": url,
                    "source": "google"
                })
                print(f"Google encontró: {url}")
        except Exception as e:
            print(f"Error en Google Search: {e}")
        return contacts

    def search_duckduckgo(self, criteria):
        contacts = []
        try:
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(criteria, max_results=3)]
                for r in results:
                    contacts.append({
                        "name": r.get("title", "Sin título"),
                        "link": r.get("href"),
                        "source": "duckduckgo"
                    })
                    print(f"DuckDuckGo encontró: {r.get('title')} - {r.get('href')}")
        except Exception as e:
            print(f"Error en DuckDuckGo Search: {e}")
        return contacts

    def scrape_contact_info(self, url, fallback_name=None):
        contact = {
            "name": fallback_name or "Sin nombre",
            "email": None,
            "phone": None, 
            "location": None,
            "website": url
        }
        
        if not url:
            return contact
            
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            print(f"Scrapeando: {url}")
            resp = requests.get(url, timeout=10, headers=headers)
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                text = soup.get_text(" ", strip=True).lower()
                
                # Extraer nombre del título
                if soup.title and soup.title.string:
                    contact["name"] = soup.title.string.strip()[:100]
                
                # Buscar email con patrón mejorado
                email_patterns = [
                    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
                ]
                for pattern in email_patterns:
                    email_match = re.search(pattern, text)
                    if email_match:
                        contact["email"] = email_match.group(0)
                        break
                
                # Buscar teléfono con patrones mejorados
                phone_patterns = [
                    r"\+507[\s-]?\d{4}[\s-]?\d{4}",  # Panamá específico
                    r"\(\d{3}\)[\s-]?\d{4}[\s-]?\d{4}",  # (507) 1234-5678
                    r"\d{3}[\s-]?\d{4}[\s-]?\d{4}",  # 507 1234 5678
                    r"\d{4}[\s-]?\d{4}",  # 1234 5678
                ]
                for pattern in phone_patterns:
                    phone_match = re.search(pattern, text)
                    if phone_match:
                        contact["phone"] = phone_match.group(0)
                        break
                
                # Buscar ubicación
                location_keywords = [
                    "panamá", "ciudad de panamá", "colón", "chiriquí", 
                    "veraguas", "herrera", "los santos", "coclé", 
                    "bocas del toro", "darién", "guna yala"
                ]
                for keyword in location_keywords:
                    if keyword in text:
                        contact["location"] = keyword.title()
                        break
                        
                print(f"Datos extraídos: {contact['name'][:30]}... - {contact['email']} - {contact['phone']}")
                
        except Exception as e:
            print(f"Error scrapeando {url}: {e}")
            
        return contact

    def fetch_external_data(self, api_endpoint):
        # This method could be used to fetch data from an external API.
        # Implement the logic to make an API call and return the results.
        pass