from googlesearch import search
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import re
import html
import unicodedata
from models.database import Contact, SearchHistory, db
from services.validator import DataValidator

class DataMiningService:
    def __init__(self):
        pass

    def clean_text(self, text):
        """
        Limpia y corrige problemas de codificación en el texto
        """
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
        
        # Remover caracteres de control excepto saltos de línea básicos
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)
        
        return text

    def search_contacts(self, criteria, save_to_db=True):
        print(f"Iniciando búsqueda para: {criteria}")
        # Dominios y palabras clave a excluir (redes sociales, mapas, directorios, etc.)
        excluded_domains = [
            'facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com', 'youtube.com',
            'tiktok.com', 'wa.me', 'web.whatsapp.com', 'pinterest.com', 'snapchat.com',
            'wikipedia.org', 'maps.google.com', 'goo.gl', 'bit.ly', 'messenger.com',
            'plus.google.com', 'tumblr.com', 'reddit.com', 'telegram.me', 't.me', 'threads.net',
            'waze.com', 'moovitapp.com', 'paginasamarillas.com', 'cybo.com', 'near-place.com',
            'miguia.com', 'todosbiz.com', 'nexdu.com', 'amerpages.com', 'panadata.net',
            'mapfre.com', 'es-biz.com', 'docati.com', 'panamaemprende.gob.pa',
            'vymaps.com'  # <--- agregado filtro para vymaps.com
        ]
        excluded_keywords = [
            'cómo llegar', 'como llegar', 'mapa', 'dirección', 'direccion', 'rutas', 'listado',
            'guía', 'guia', 'horarios', 'sucursales', 'listado', 'fichas', 'mi guía', 'mi guia',
            'páginas amarillas', 'paginas amarillas', 'directorio', 'ubicación', 'ubicacion', 'media/'
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
        # --- NUEVO: deduplicación por dominio principal en la búsqueda actual ---
        dominios_vistos = set()
        # --- FIN NUEVO ---
        for i, result in enumerate(all_results):
            url = result.get('link')
            # Filtrar resultados no deseados
            if not url or any(domain in url for domain in excluded_domains):
                print(f"❌ URL excluida por dominio irrelevante: {url}")
                continue
            # Filtro por palabras clave irrelevantes en nombre o url
            nombre_resultado = (result.get('name') or '').lower()
            if any(kw in nombre_resultado for kw in excluded_keywords) or any(kw in url.lower() for kw in excluded_keywords):
                print(f"❌ URL excluida por palabra clave irrelevante: {url}")
                continue
            if url.startswith('/search?') or url.startswith('https://www.google.com/search?'):
                print(f"❌ URL excluida por ser resultado de Google Search: {url}")
                continue
            # Evitar repetir scraping en la misma búsqueda
            if url in scraped_urls:
                print(f"⚠️ URL ya scrapeada en esta búsqueda: {url}")
                continue
            # --- NUEVO: Omitir URLs ya presentes en la base de datos antes de scrapear ---
            url_normalizada = url.strip().lower()
            url_ya_guardada = Contact.query.filter(Contact.website == url_normalizada).first()
            if url_ya_guardada:
                print(f"⚠️ URL omitida por ya estar en la base de datos: {url}")
                continue
            # --- FIN NUEVO ---
            # --- deduplicación por dominio principal en la búsqueda actual ---
            from services.validator import DataValidator
            dominio_actual = DataValidator.extract_domain(url)
            if dominio_actual in dominios_vistos:
                print(f"⚠️ Dominio ya visto en esta búsqueda: {dominio_actual}")
                continue
            dominios_vistos.add(dominio_actual)
            # --- FIN NUEVO ---
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
            if not is_dup and save_to_db:
                # Guardar en base de datos solo si save_to_db=True
                new_contact = Contact(
                    name=self.clean_text(contact_data.get('name', 'Sin nombre')),
                    email=contact_data.get('email'),
                    phone=contact_data.get('phone'),
                    location=self.clean_text(contact_data.get('location')),
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
            elif is_dup:
                print(f"⚠️ Contacto duplicado en base de datos omitido: {dup_msg}")
            # --- FILTRO: Solo agregar contactos con datos relevantes ---
            nombre = (contact_data.get('name') or '').strip()
            tiene_dato_util = (
                (contact_data.get('email') and contact_data.get('email') != 'No disponible') or
                (contact_data.get('phone') and contact_data.get('phone') != 'No disponible') or
                (contact_data.get('location') and contact_data.get('location') != 'No disponible') or
                (nombre and not nombre.lower().startswith('resultado de google'))
            )
            if not tiene_dato_util:
                print(f"❌ Contacto omitido por no tener datos útiles: {contact_data}")
                continue
            # --- FIN FILTRO ---
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
            for url in search(criteria, num_results=15, lang="es"):
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
                results = [r for r in ddgs.text(criteria, max_results=15)]
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
            "name": self.clean_text(fallback_name) if fallback_name else "Sin nombre",
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
                    raw_name = soup.title.string.strip()[:100]
                    contact["name"] = self.clean_text(raw_name)
                
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

    def search_contacts_limited(self, criteria, max_results=5, save_to_db=True):
        """
        Versión limitada de search_contacts para evitar timeouts en recomendaciones automáticas
        """
        print(f"Iniciando búsqueda limitada para: {criteria} (máximo {max_results} resultados)")
        
        # Dominios excluidos (versión reducida para mejor rendimiento)
        excluded_domains = [
            'facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com', 'youtube.com',
            'maps.google.com', 'wikipedia.org', 'paginasamarillas.com'
        ]
        
        contacts = []
        new_contacts_count = 0
        scraped_count = 0
        
        try:
            # Buscar solo en Google para ser más rápido
            google_results = self.search_google_scrape_limited(criteria, max_results)
            
            for i, result in enumerate(google_results):
                if scraped_count >= max_results:
                    break
                    
                url = result.get('link')
                
                # Filtros básicos
                if not url or any(domain in url for domain in excluded_domains):
                    continue
                
                # Verificar si ya existe en BD
                url_normalizada = url.strip().lower()
                if Contact.query.filter(Contact.website == url_normalizada).first():
                    continue
                
                try:
                    print(f"Procesando resultado {scraped_count + 1}: {url}")
                    contact_data = self.scrape_contact_info_limited(url, result.get('name'))
                    contact_data['search_query'] = criteria
                    contact_data['source'] = result.get('source', 'google')
                    
                    # Validación básica
                    from services.validator import DataValidator
                    email_valid, email_msg = DataValidator.validate_email(contact_data.get('email'))
                    phone_valid, phone_msg = DataValidator.validate_phone(contact_data.get('phone'))
                    
                    contact_data['email_valid'] = email_valid
                    contact_data['phone_valid'] = phone_valid
                    contact_data['quality_score'] = DataValidator.calculate_quality_score(contact_data)
                    
                    # Guardar en BD si es nuevo y válido
                    if save_to_db and contact_data.get('quality_score', 0) > 30:
                        try:
                            new_contact = Contact(
                                name=self.clean_text(contact_data.get('name', 'Sin nombre')),
                                email=contact_data.get('email'),
                                phone=contact_data.get('phone'),
                                location=self.clean_text(contact_data.get('location')),
                                website=contact_data.get('website'),
                                search_query=criteria,
                                source=contact_data.get('source'),
                                quality_score=contact_data.get('quality_score', 0),
                                email_valid=email_valid,
                                phone_valid=phone_valid
                            )
                            db.session.add(new_contact)
                            db.session.commit()
                            new_contacts_count += 1
                            print(f"✅ Contacto guardado: {contact_data.get('name')}")
                        except Exception as e:
                            print(f"❌ Error guardando contacto: {e}")
                            db.session.rollback()
                    
                    contacts.append(contact_data)
                    scraped_count += 1
                    
                except Exception as e:
                    print(f"Error procesando {url}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error en búsqueda limitada: {e}")
            return []
        
        # Guardar historial
        try:
            search_history = SearchHistory(query=criteria, results_found=len(contacts))
            db.session.add(search_history)
            db.session.commit()
        except Exception as e:
            print(f"Error guardando historial: {e}")
        
        print(f"Búsqueda limitada completada: {len(contacts)} contactos, {new_contacts_count} nuevos")
        return contacts
    
    def search_google_scrape_limited(self, criteria, max_results=5):
        """Búsqueda limitada en Google"""
        contacts = []
        try:
            count = 0
            for url in search(criteria, num_results=max_results, lang="es"):
                if count >= max_results:
                    break
                contacts.append({
                    "name": f"Resultado de Google: {url[:50]}...",
                    "link": url,
                    "source": "google"
                })
                print(f"Google encontró: {url}")
                count += 1
        except Exception as e:
            print(f"Error en Google Search limitado: {e}")
        return contacts
    
    def scrape_contact_info_limited(self, url, fallback_name=None):
        """Scraping limitado y más rápido"""
        contact = {
            "name": self.clean_text(fallback_name) if fallback_name else "Sin nombre",
            "email": None,
            "phone": None, 
            "location": None,
            "website": url
        }
        
        try:
            # Timeout reducido para evitar bloqueos
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar nombre (título de la página)
                title = soup.find('title')
                if title and title.text.strip():
                    raw_title = title.text.strip()[:100]
                    contact['name'] = self.clean_text(raw_title)
                
                # Buscar email (solo primer match)
                text_content = soup.get_text()
                email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text_content)
                if email_match:
                    contact['email'] = email_match.group()
                
                # Buscar teléfono (solo primer match)
                phone_patterns = [
                    r'\b\d{4}-\d{4}\b',  # 1234-5678
                    r'\b\d{3}-\d{4}\b',  # 123-4567
                    r'\+507[- ]?\d{4}[- ]?\d{4}',  # +507 1234 5678
                ]
                for pattern in phone_patterns:
                    phone_match = re.search(pattern, text_content)
                    if phone_match:
                        contact['phone'] = phone_match.group()
                        break
                        
        except Exception as e:
            print(f"Error scraping {url}: {e}")
        
        return contact