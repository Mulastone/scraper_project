import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import unicodedata
from ..database.operations import PropertyRepository
from ..database.connection import create_tables
from ..utils.text_cleaner import limpiar_texto, extraer_precio

class ClausScraper:
    def __init__(self):
        self.base_url = "http://www.7claus.com"
        self.listing_url = "http://www.7claus.com/cercador/pisos_duplex_apartaments_atics/andorra_andorra/"
        self.website = "www.7claus.com"
        
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
            
            # Extraer características (habitaciones, baños, superficie)
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
                            data['surface'] = int(value)
                        except (ValueError, TypeError):
                            data['surface'] = 0
            
            # URL de detalle desde el botón de contacto
            btn_contacto = card.find('div', class_='btnContacto')
            if btn_contacto and btn_contacto.get('data-url'):
                detail_path = btn_contacto['data-url'].split('#')[0]
                data['url'] = f"{self.base_url}{detail_path}"
            
            # Extraer ubicación del título
            if data['title'] != 'N/A':
                # El título suele tener formato "Pis a Carrer Sant Jordi"
                if ' a ' in data['title']:
                    parts = data['title'].split(' a ', 1)
                    if len(parts) > 1:
                        data['location'] = limpiar_texto(parts[1])
            
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