import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import unicodedata
from ..database.operations import PropertyRepository
from ..database.connection import create_tables
from ..utils.text_cleaner import limpiar_texto, extraer_precio, detectar_pas_de_la_casa, detectar_arinsal, detectar_bordes

class ClausScraper:
    def __init__(self):
        self.base_url = "http://www.7claus.com"
        self.listing_url = "http://www.7claus.com/cercador/pisos_duplex_apartaments_atics/andorra_andorra/"
        self.website = "www.7claus.com"
        
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
        """
        Ejecuta el scraper principal
        """
        # Crear tablas si no existen
        create_tables()
        
        # Obtener las propiedades
        propiedades = self.obtener_propiedades()
        
        # Procesar cada propiedad
        property_repo = PropertyRepository()
        propiedades_procesadas = 0
        
        for propiedad in propiedades:
            try:
                # Extraer datos de la propiedad
                property_data = self.extract_property_data(propiedad)
                
                if property_data:
                    # Guardar la propiedad
                    if property_repo.save_property(property_data):
                        propiedades_procesadas += 1
                        print(f"✅ Propiedad guardada: {property_data.get('titulo', 'Sin título')[:50]}...")
                    else:
                        print(f"❌ Error al guardar: {property_data.get('titulo', 'Sin título')[:50]}...")
                        
            except Exception as e:
                print(f"Error procesando propiedad: {e}")
        
        print(f"🏁 Scraping completado. {propiedades_procesadas} propiedades procesadas")

    def obtener_propiedades(self):
        """Obtiene la lista de propiedades de la página de listado"""
        try:
            print(f"Obteniendo propiedades de: {self.listing_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(self.listing_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            cards = soup.find_all('div', class_='cardAnuncio')
            
            print(f"Encontradas {len(cards)} propiedades")
            return cards
            
        except requests.RequestException as e:
            print(f"Error al obtener propiedades: {e}")
            return []

    def get_property_description(self, url_inmueble):
        """
        Obtiene la descripción completa de una propiedad específica
        """
        try:
            response = requests.get(url_inmueble, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar la descripción en diferentes posibles ubicaciones
            descripcion = ""
            
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
            
            return descripcion.strip()
            
        except Exception as e:
            print(f"Error al obtener descripción de {url_inmueble}: {e}")
            return ""

    def extract_property_data(self, card):
        """Extrae los datos de una propiedad individual"""
        try:
            data = {
                'website': self.website,
                'timestamp': datetime.now(),
                'operation': 'Venta',  # La URL indica "en_venda"
                'address': 'N/A',
                'reference': 'N/A',
                'title': 'N/A',
                'location': 'N/A',
                'price': 0,
                'rooms': 0,
                'bathrooms': 0,
                'surface': 0,
                'url': 'N/A'
            }
            
            # Título
            titulo_elem = card.find('span', class_='titulo')
            if titulo_elem:
                data['title'] = limpiar_texto(titulo_elem.get_text())
            
            # Referencia
            ref_elem = card.find('span', class_='contRef')
            if ref_elem:
                data['reference'] = limpiar_texto(ref_elem.get_text())
            
            # Precio
            precio_elem = card.find('div', class_='precio')
            if precio_elem:
                precio_text = precio_elem.get_text().strip().split('\n')[0].strip()
                data['price'] = extraer_precio(precio_text)
            
            # FILTRO 1: Saltar propiedades con precio mayor a 450,000€
            if data['price'] > 450000:
                print(f"⚠️ [CLAUS] Propiedad filtrada por precio alto: {data['price']:,.0f}€ > 450,000€")
                return None
            
            # Extraer ubicación del título ANTES del filtro de Andorra
            if data['title'] != 'N/A':
                # El título suele tener formato "Pis a Carrer Sant Jordi"
                if ' a ' in data['title']:
                    parts = data['title'].split(' a ', 1)
                    if len(parts) > 1:
                        data['location'] = limpiar_texto(parts[1])
                
            # FILTRO 2: Verificar que la propiedad esté en Andorra ANTES de detectar poblaciones especiales
            if not self.is_andorra_location(data['location']):
                print(f"🌍 [CLAUS] Propiedad filtrada por estar fuera de Andorra: {data['location']}")
                return None            # Extraer características (habitaciones, baños, superficie)
            props = card.find_all('li')
            for prop in props:
                divs = prop.find_all('div')
                if len(divs) == 2:
                    key = divs[0].get_text().strip()
                    value = divs[1].get_text().strip()
                    
                    if 'Habs' in key:
                        try:
                            data['rooms'] = int(value)
                        except (ValueError, TypeError):
                            data['rooms'] = 0
                    elif 'Banys' in key:
                        try:
                            data['bathrooms'] = int(value)
                        except (ValueError, TypeError):
                            data['bathrooms'] = 0
                    elif 'm²' in key or 'm2' in key:
                        try:
                            # Soportar decimales (coma o punto)
                            value_clean = value.replace(',', '.')
                            data['surface'] = float(value_clean)
                        except (ValueError, TypeError):
                            data['surface'] = 0
            
            # URL de detalle desde el botón de contacto
            btn_contacto = card.find('div', class_='btnContacto')
            if btn_contacto and btn_contacto.get('data-url'):
                detail_path = btn_contacto['data-url'].split('#')[0]
                data['url'] = f"{self.base_url}{detail_path}"
            
            # FILTRO 3: Detectar poblaciones especiales DESPUÉS de confirmar que está en Andorra
            
            # Verificar Pas de la Casa (Encamp o ubicaciones genéricas)
            if data['location'] and ('encamp' in data['location'].lower() or 'andorra' in data['location'].lower() or data['location'] == 'N/A'):
                print(f"🔍 [CLAUS] Verificando descripción para posible Pas de la Casa: {data['url']}")
                descripcion = self.get_property_description(data['url'])
                
                if descripcion and detectar_pas_de_la_casa(descripcion):
                    print(f"✅ [CLAUS] ¡Detectado Pas de la Casa en descripción! Cambiando ubicación de '{data['location']}' a 'Pas de la Casa'")
                    data['location'] = "Pas de la Casa"
                else:
                    print(f"❌ [CLAUS] No se detectó Pas de la Casa en la descripción")
            
            # Verificar Arinsal (La Massana o Arinsal directo)
            elif data['location'] and ('massana' in data['location'].lower() or 'arinsal' in data['location'].lower()):
                print(f"🔍 [CLAUS] Verificando descripción para posible Arinsal: {data['url']}")
                descripcion = self.get_property_description(data['url'])
                
                if descripcion and detectar_arinsal(descripcion):
                    print(f"✅ [CLAUS] ¡Detectado Arinsal en descripción! Cambiando ubicación de '{data['location']}' a 'Arinsal'")
                    data['location'] = "Arinsal"
                else:
                    print(f"❌ [CLAUS] No se detectó Arinsal en la descripción")
            
            # Verificar Bordes d'Envalira (Canillo, Soldeu, etc.)
            elif data['location'] and ('canillo' in data['location'].lower() or 'soldeu' in data['location'].lower() or 
                                     'incles' in data['location'].lower() or 'tarter' in data['location'].lower() or
                                     'bordes' in data['location'].lower()):
                print(f"🔍 [CLAUS] Verificando descripción para posible Bordes d'Envalira: {data['url']}")
                descripcion = self.get_property_description(data['url'])
                
                if descripcion and detectar_bordes(descripcion):
                    print(f"✅ [CLAUS] ¡Detectado Bordes d'Envalira en descripción! Cambiando ubicación de '{data['location']}' a 'Bordes d\\'Envalira'")
                    data['location'] = "Bordes d'Envalira"
                else:
                    print(f"❌ [CLAUS] No se detectó Bordes d'Envalira en la descripción")
            else:
                print(f"ℹ️ [CLAUS] Ubicación '{data['location']}' no necesita verificación")
            
            # Verificar que tenemos datos mínimos
            if data['title'] == 'N/A' or data['price'] == 0:
                return None
                
            return data
            
        except Exception as e:
            print(f"Error al extraer datos de propiedad: {e}")
            return None


if __name__ == "__main__":
    print("🏠 Iniciando scraper de 7 Claus...")
    scraper = ClausScraper()
    scraper.run()
    print("✨ Scraping de 7 Claus completado")