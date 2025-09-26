import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ..database.operations import PropertyRepository
from ..database.connection import create_tables
from ..utils.text_cleaner import limpiar_texto, extraer_precio

class PisosAdScraper:
    def __init__(self):
        self.base_url = "https://pisos.ad"
        self.website = "pisos.ad"
        self.start_url = (
            "https://pisos.ad/venda/tots-els-tipus/tots-subtipus?&minrooms=0&minbanys=0&maxrooms=0&maxbanys=0&minmetres=0&minprice=0&maxprice=0&reference=&caracteristiques=&order=&immo=0&parro=0&promocions=false"
        )

    def run(self):
        create_tables()
        page = 1
        total_saved = 0
        
        while page <= 5:  # Limitar a 5 páginas para testing
            url = self.start_url + f"&page={page}"
            print(f"Scraping página {page}: {url}")
            
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'})
            if resp.status_code != 200:
                print(f"Error HTTP {resp.status_code} en página {page}")
                break
                
            soup = BeautifulSoup(resp.content, "html.parser")
            
            # Buscar enlaces de propiedades específicas (no páginas de listado)
            property_links = soup.find_all("a", href=True)
            property_urls = []
            
            for link in property_links:
                href = link.get("href", "")
                # Filtrar solo URLs de propiedades individuales
                if ("/venda/" in href and 
                    href not in property_urls and
                    not href.startswith("http") and  # Evitar enlaces externos
                    not "wa.me" in href and          # Evitar WhatsApp
                    not "tel:" in href and           # Evitar teléfonos
                    not "mailto:" in href and        # Evitar emails
                    not href.endswith("/tots-subtipus") and
                    not href.endswith("/venda") and
                    len(href.split("/")) >= 3 and
                    href.split("/")[-1].isdigit()):  # Debe terminar en número (ID)
                    property_urls.append(href)
            
            print(f"Encontrados {len(property_urls)} enlaces de propiedades")
            
            if not property_urls:
                print(f"No se encontraron propiedades en página {page}")
                break
                
            for prop_url in property_urls[:3]:  # Limitar a 3 por página para testing
                try:
                    data = self.extract_property_from_url(prop_url)
                    if data:
                        PropertyRepository.save_property(data)
                        total_saved += 1
                        print(f"Guardada propiedad: {data['title'][:50]}...")
                except Exception as e:
                    print(f"Error procesando {prop_url}: {e}")
                    continue
                    
            page += 1
            
        print(f"Total propiedades guardadas: {total_saved}")

    def extract_property_from_url(self, relative_url):
        """Extrae datos de una propiedad individual"""
        # Filtrar URLs que no son de propiedades individuales
        if not relative_url or relative_url in ["/venda/tots-els-tipus/tots-subtipus", "/", "#"]:
            return None
            
        full_url = f"https://pisos.ad{relative_url}" if not relative_url.startswith("http") else relative_url
        
        try:
            resp = requests.get(full_url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'})
            if resp.status_code != 200:
                return None
                
            soup = BeautifulSoup(resp.content, "html.parser")
            
            # Extraer título - buscar en diferentes lugares
            title = "Sin título"
            title_selectors = ["h1", "h2", ".property-title", ".listing-title"]
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            # Si no encuentra título, usar el de la URL
            if title == "Sin título" or len(title) < 10:
                url_parts = relative_url.strip("/").split("/")
                if len(url_parts) >= 2:
                    title = url_parts[-1].replace("-", " ").title()
            
            # Extraer precio - buscar en diferentes formatos
            price = 0
            page_text = soup.get_text()
            
            import re
            # Buscar patrones de precio
            price_patterns = [
                r'([\d.,]+)\s*€',
                r'€\s*([\d.,]+)',
                r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*euros?',
            ]
            
            for pattern in price_patterns:
                price_match = re.search(pattern, page_text, re.IGNORECASE)
                if price_match:
                    price_str = price_match.group(1).replace(",", "").replace(".", "")
                    try:
                        price = int(price_str)
                        if price > 1000:  # Filtrar precios muy bajos que pueden ser errores
                            break
                    except:
                        continue
            
            # Extraer detalles (habitaciones, baños, superficie)
            rooms = bathrooms = surface = 0
            
            # Habitaciones
            rooms_patterns = [
                r'(\d+)\s*habitacion',
                r'(\d+)\s*hab\b',
                r'(\d+)\s*dormitori'
            ]
            for pattern in rooms_patterns:
                rooms_match = re.search(pattern, page_text, re.IGNORECASE)
                if rooms_match:
                    rooms = int(rooms_match.group(1))
                    break
            
            # Baños
            banys_patterns = [
                r'(\d+)\s*bany',
                r'(\d+)\s*lavabo',
                r'(\d+)\s*wc'
            ]
            for pattern in banys_patterns:
                banys_match = re.search(pattern, page_text, re.IGNORECASE)
                if banys_match:
                    bathrooms = int(banys_match.group(1))
                    break
            
            # Superficie
            surface_patterns = [
                r'(\d+)\s*m[²2]',
                r'(\d+)\s*metre',
                r'(\d+)\s*sq'
            ]
            for pattern in surface_patterns:
                surface_match = re.search(pattern, page_text, re.IGNORECASE)
                if surface_match:
                    surface = int(surface_match.group(1))
                    break
            
            # Extraer ubicación del título o URL
            location = ""
            # Intentar extraer de la URL
            location_patterns = [
                r'/([^/]+)/(\d+)$',  # .../location/id
                r'/([^/]+)/?$'       # .../location
            ]
            
            for pattern in location_patterns:
                location_match = re.search(pattern, relative_url)
                if location_match:
                    location = location_match.group(1).replace("-", " ").title()
                    break
            
            # Si no encontró ubicación, intentar del título
            if not location and "venda" in title.lower():
                location_in_title = re.search(r'a\s+([A-Za-z\s]+)', title, re.IGNORECASE)
                if location_in_title:
                    location = location_in_title.group(1).strip()
            
            return {
                "reference": relative_url.split("/")[-1] or str(hash(full_url))[-8:],
                "operation": "venta",
                "price": price,
                "rooms": rooms,
                "bathrooms": bathrooms,
                "surface": surface,
                "title": limpiar_texto(title),
                "location": limpiar_texto(location) if location else "Andorra",
                "address": limpiar_texto(location) if location else "Andorra",
                "url": full_url,
                "website": self.website,
            }
            
        except Exception as e:
            print(f"Error extrayendo datos de {full_url}: {e}")
            return None

if __name__ == "__main__":
    PisosAdScraper().run()
