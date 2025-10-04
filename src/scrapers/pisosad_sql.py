import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from ..database.operations import PropertyRepository
from ..database.connection import create_tables
from ..utils.text_cleaner import limpiar_texto, extraer_precio, detectar_pas_de_la_casa, detectar_arinsal, detectar_bordes

class PisosAdScraper:
    def __init__(self):
        self.base_url = "https://pisos.ad"
        self.website = "pisos.ad"
        # URLs para diferentes rangos de precio - MÁXIMO 450,000€
        self.start_urls = [
            # Propiedades más accesibles (10k-300k) - RANGO PRINCIPAL
            "https://pisos.ad/venda/tots-els-tipus/tots-subtipus?&minrooms=0&minbanys=0&maxrooms=0&maxbanys=0&minmetres=0&minprice=10000&maxprice=300000&reference=&caracteristiques=&order=&immo=0&parro=0&promocions=false",
            # Propiedades de rango medio-alto (300k-450k)
            "https://pisos.ad/venda/tots-els-tipus/tots-subtipus?&minrooms=0&minbanys=0&maxrooms=0&maxbanys=0&minmetres=0&minprice=300000&maxprice=450000&reference=&caracteristiques=&order=&immo=0&parro=0&promocions=false"
        ]
        
        # Ubicaciones válidas de Andorra
        self.andorra_keywords = [
            'andorra', 'escaldes', 'engordany', 'sant julia', 'encamp', 'canillo', 
            'massana', 'ordino', 'pas de la casa', 'arinsal', 'bordes', 'envalira',
            'tarter', 'soldeu', 'incles', 'pal', 'serrat', 'les bons', 'santa coloma',
            'erts', 'llorts', 'sispony', 'ransol', 'aixovall', 'nagol'
        ]
    
    def is_andorra_location(self, location):
        """
        Verifica si una ubicación pertenece a Andorra
        """
        if not location or location == 'N/A':
            return False
            
        location_lower = location.lower()
        
        # Verificar si contiene alguna palabra clave de Andorra
        return any(keyword in location_lower for keyword in self.andorra_keywords)

    def run(self):
        create_tables()
        total_saved = 0
        
        # Scraper multiple rangos de precio para mayor variedad
        for url_index, start_url in enumerate(self.start_urls):
            price_range = ["€10k-€300k", "€300k-€450k"][url_index]
            print(f"\n🎯 SCRAPING RANGO {price_range}")
            print("=" * 50)
            
            page = 1
            range_properties = []  # Lista para acumular propiedades del rango
            
            # Más páginas para el rango principal (€10k-€300k)
            max_pages = 15 if url_index == 0 else 8  # 15 páginas para rango principal, 8 para el segundo
            
            while page <= max_pages:
                url = start_url + f"&page={page}"
                print(f"Scraping {price_range} página {page}")
                
                resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'})
                if resp.status_code != 200:
                    print(f"Error HTTP {resp.status_code} en página {page}")
                    break
                    
                soup = BeautifulSoup(resp.content, "html.parser")
                
                # Buscar enlaces de propiedades específicas
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
                
                print(f"Encontrados {len(property_urls)} enlaces de propiedades en {price_range}")
                
                if not property_urls:
                    print(f"No se encontraron propiedades en página {page}")
                    break
                    
                # Extraer datos de propiedades (sin guardar aún)
                for prop_url in property_urls[:15]:  # 15 propiedades por página para mayor cobertura
                    try:
                        data = self.extract_property_from_url(prop_url)
                        if data:
                            range_properties.append(data)
                            print(f"Extraída: €{data['price']:,} - {data['title'][:40]}...")
                    except Exception as e:
                        print(f"Error procesando {prop_url}: {e}")
                        continue
                        
                page += 1
            
            # Guardar todas las propiedades del rango en lote
            if range_properties:
                range_saved = PropertyRepository.save_properties_batch(range_properties)
                total_saved += range_saved
                print(f"✅ Rango {price_range}: {range_saved} propiedades guardadas en lote")
            else:
                print(f"⚠️ Rango {price_range}: No se encontraron propiedades válidas")
            
        print(f"\n🎯 TOTAL PROPIEDADES GUARDADAS: {total_saved}")

    def get_property_description(self, full_url):
        """
        Obtiene la descripción completa de una propiedad específica
        """
        try:
            response = requests.get(full_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'})
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # BÚSQUEDA PRIORITARIA: Primero buscar descripciones específicas que mencionen "Pas de la Casa"
            descripcion = ""
            import re
            
            # Buscar directamente en el HTML crudo por contenido específico
            html_content = response.content.decode('utf-8', errors='ignore')
            
            # Si la página contiene "Pas de la Casa", priorizar esa descripción
            if 'Pas de la Casa' in html_content:
                # Estrategia 1: Buscar desde "Busques" hasta "perfecta"
                match = re.search(r'Busques una inversió.*?perfecta', html_content, re.DOTALL | re.IGNORECASE)
                if match and 'Pas de la Casa' in match.group(0):
                    descripcion = match.group(0)
                
                # Estrategia 2: Si no funciona, buscar líneas que contengan "Pas de la Casa"
                if not descripcion:
                    lines = html_content.split('\n')
                    for line in lines:
                        if 'Pas de la Casa' in line and len(line) > 200:
                            descripcion = line
                            break
            
            # BÚSQUEDA ESTÁNDAR: Si no hay "Pas de la Casa", usar métodos convencionales
            if not descripcion:
                # Buscar en div de descripción
                desc_div = soup.find('div', class_='descripcion')
                if desc_div:
                    descripcion = desc_div.get_text(strip=True)
                
                # Si no se encontró, buscar por otros selectores comunes
                if not descripcion:
                    # Buscar en párrafos largos
                    paragrafos = soup.find_all('p')
                    for p in paragrafos:
                        texto = p.get_text(strip=True)
                        if len(texto) > 100:
                            descripcion += " " + texto
                
                # También buscar en divs que contengan mucho texto
                if not descripcion:
                    divs = soup.find_all('div')
                    for div in divs:
                        texto = div.get_text(strip=True)
                        if len(texto) > 200 and ('ubicación' in texto.lower() or 'situado' in texto.lower()):
                            descripcion = texto
                            break
            
            # PROCESAMIENTO FINAL: Limpiar el texto encontrado
            if descripcion:
                descripcion = descripcion.replace('~~', '. ').replace('\\n', ' ').replace('\\t', ' ')
                # Decodificar entidades HTML
                import html
                descripcion = html.unescape(descripcion).strip()
            
            return descripcion.strip()
            
        except Exception as e:
            print(f"Error al obtener descripción de {full_url}: {e}")
            return ""

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
            
            # Extraer precio - buscar el precio principal en el HTML
            price = 0
            page_text = soup.get_text()
            
            # Buscar específicamente el patrón del precio principal
            # En pisos.ad aparece como: TÍTULO   \rPRECIO €\r \r[precio/m2] €/m2
            price_patterns = [
                r'(?:VENDA|venda).*?\r(\d+(?:\.\d{3})*)\s*€\r',  # Patrón específico de pisos.ad
                r'\r(\d+(?:\.\d{3})*)\s*€\r\s*\r[\d,]+\s*€/m2', # Precio seguido de precio/m2
                r'(?:PIS|XALET|CASA|TERRENY).*?\r(\d+(?:\.\d{3})*)\s*€\r', # Tipos de propiedad + precio
                r'^.*?(\d{3}(?:\.\d{3})+)\s*€.*?€/m2',          # Precio grande seguido de precio/m2
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    price_str = match.group(1).replace('.', '')  # Remove thousands separators
                    try:
                        price = int(price_str)
                        if price > 50000:  # Precio mínimo razonable
                            break
                    except:
                        continue
            
            # Si no encuentra con patrones específicos, usar extracción general de la primera parte
            if price == 0:
                # Buscar en los primeros 3000 caracteres donde suele estar el precio principal
                first_part = page_text[:3000]
                extracted_price = extraer_precio(first_part)
                if extracted_price and 50000 <= extracted_price <= 50000000:  # Rango razonable
                    price = int(extracted_price)
            
            # EXTRAER UBICACIÓN PRIMERO (antes de filtros)
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
                    
            # Si no se extrae de URL, intentar del título
            if not location:
                location = title
            
            # FILTRO 1: Saltar propiedades con precio mayor a 450,000€
            if price > 450000:
                print(f"⚠️ [PISOSAD] Propiedad filtrada por precio alto: {price:,.0f}€ > 450,000€")
                return None
            
            # FILTRO 2: Verificar que la propiedad esté en Andorra ANTES de detectar poblaciones especiales
            if not self.is_andorra_location(location):
                print(f"🌍 [PISOSAD] Propiedad filtrada por estar fuera de Andorra: {location}")
                return None
            
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
            
            # Superficie - MEJORADO para capturar decimales
            surface_patterns = [
                r'(\d+[,.]?\d*)\s*m[²2]',  # Captura decimales como 46,92 o 46.92
                r'(\d+[,.]?\d*)\s*metre',
                r'(\d+[,.]?\d*)\s*sq'
            ]
            for pattern in surface_patterns:
                surface_match = re.search(pattern, page_text, re.IGNORECASE)
                if surface_match:
                    # Convertir coma a punto para float
                    surface_str = surface_match.group(1).replace(',', '.')
                    surface = float(surface_str)
                    break
            
            # NUEVA LÓGICA: Verificar descripción para ubicaciones específicas
            final_location = location if location else "Andorra"
            
            # Verificar Pas de la Casa (Encamp o ubicaciones genéricas)
            if final_location and ('encamp' in final_location.lower() or 'andorra' == final_location.lower()):
                print(f"🔍 [PISOSAD] Verificando descripción para posible Pas de la Casa: {full_url}")
                descripcion = self.get_property_description(full_url)
                
                if descripcion and detectar_pas_de_la_casa(descripcion):
                    print(f"✅ [PISOSAD] ¡Detectado Pas de la Casa en descripción! Cambiando ubicación de '{final_location}' a 'Pas de la Casa'")
                    final_location = "Pas de la Casa"
                else:
                    print(f"❌ [PISOSAD] No se detectó Pas de la Casa en la descripción")
            
            # Verificar Arinsal (La Massana o Arinsal directo)
            elif final_location and ('massana' in final_location.lower() or 'arinsal' in final_location.lower()):
                print(f"🔍 [PISOSAD] Verificando descripción para posible Arinsal: {full_url}")
                descripcion = self.get_property_description(full_url)
                
                if descripcion and detectar_arinsal(descripcion):
                    print(f"✅ [PISOSAD] ¡Detectado Arinsal en descripción! Cambiando ubicación de '{final_location}' a 'Arinsal'")
                    final_location = "Arinsal"
                else:
                    print(f"❌ [PISOSAD] No se detectó Arinsal en la descripción")
            
            # Verificar Bordes d'Envalira (Canillo, Soldeu, Incles, etc.)
            elif final_location and ('canillo' in final_location.lower() or 'soldeu' in final_location.lower() or 
                                   'incles' in final_location.lower() or 'tarter' in final_location.lower() or
                                   'bordes' in final_location.lower()):
                print(f"🔍 [PISOSAD] Verificando descripción para posible Bordes d'Envalira: {full_url}")
                descripcion = self.get_property_description(full_url)
                
                if descripcion and detectar_bordes(descripcion):
                    print(f"✅ [PISOSAD] ¡Detectado Bordes d'Envalira en descripción! Cambiando ubicación de '{final_location}' a 'Bordes d\\'Envalira'")
                    final_location = "Bordes d'Envalira"
                else:
                    print(f"❌ [PISOSAD] No se detectó Bordes d'Envalira en la descripción")
            else:
                print(f"ℹ️ [PISOSAD] Ubicación '{final_location}' no necesita verificación")
            
            return {
                "reference": relative_url.split("/")[-1] or str(hash(full_url))[-8:],
                "operation": "venta",
                "price": price,
                "rooms": rooms,
                "bathrooms": bathrooms,
                "surface": surface,
                "title": limpiar_texto(title),
                "location": limpiar_texto(final_location),
                "address": limpiar_texto(final_location),
                "url": full_url,
                "website": self.website,
            }
            
        except Exception as e:
            print(f"Error extrayendo datos de {full_url}: {e}")
            return None

if __name__ == "__main__":
    PisosAdScraper().run()
