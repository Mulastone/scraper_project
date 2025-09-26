import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import unicodedata
from ..database.operations import PropertyRepository
from ..database.connection import create_tables
from ..utils.text_cleaner import limpiar_texto, extraer_precio

class FinquesmarquesScraper:
    def __init__(self):
        self.base_url = "https://www.finquesmarca.com"
        self.website = "www.finquesmarca.com"
        
    def run(self):
        """
        Ejecuta el scraper principal
        """
        # Crear tablas si no existen
        create_tables()
        
        url = f"{self.base_url}/cercador/?Referencia=&CampoOrden=publicacion&DireccionOrden=desc&AnunciosPorParrilla=120"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Encontrar todas las propiedades, omitiendo las que están dentro de un div con clase 'img'
            propiedades = soup.find_all('a', class_='url-inmueble')
            propiedades_filtradas = [p for p in propiedades if not p.find_parent('div', class_='img')]
            
            urls_unicas = set()
            
            for propiedad in propiedades_filtradas:
                try:
                    property_data = self.extract_property_data(propiedad, urls_unicas)
                    if property_data:
                        PropertyRepository.save_property(property_data)
                        
                except Exception as e:
                    print(f"Error al procesar una propiedad: {e}")
                    continue
                    
            print(f"Scraping completado. Procesadas {len(urls_unicas)} propiedades únicas.")
            
        except Exception as e:
            print(f"Error en el scraper: {e}")
    
    def scrape_page(self, url):
        """
        Scraper para una página específica (usado para testing)
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            propiedades = soup.find_all('div', class_='card')
            
            # Filtrar artículos que no contienen propiedades
            propiedades_filtradas = [
                p for p in propiedades 
                if not (p.find('img') and 'finquesmarca' in p.find('img').get('src', ''))
            ]
            
            urls_unicas = set()
            scraped_data = []
            
            for propiedad in propiedades_filtradas:
                try:
                    property_data = self.extract_property_data(propiedad, urls_unicas)
                    if property_data:
                        scraped_data.append(property_data)
                        
                except Exception as e:
                    print(f"Error al procesar una propiedad: {e}")
                    continue
            
            return scraped_data
            
        except Exception as e:
            print(f"Error al scraper la página {url}: {e}")
            return []
    
    def extract_property_data(self, propiedad, urls_unicas):
        """
        Extrae los datos de una propiedad
        """
        # propiedad YA ES el elemento a.url-inmueble, no necesitamos buscarlo
        url_inmueble = propiedad.get('data-path', 'N/A')
        
        if url_inmueble == 'N/A':
            return None
            
        url_inmueble = f"{self.base_url}{url_inmueble}"
        
        if url_inmueble in urls_unicas:
            return None
            
        urls_unicas.add(url_inmueble)
        
        # Buscar en el contenedor padre (div.card)
        contenedor = propiedad.find_parent('div', class_='card')
        if not contenedor:
            return None
        
        # Inicializar variables
        titulo = referencia = operacion = direccion = poblacion = 'N/A'
        precio = habitaciones = baños = superficie = 0
        
        # Extraer título del contenedor
        titulo_tag = contenedor.find('span', class_='contTitulo')
        if titulo_tag:
            titulo = limpiar_texto(titulo_tag.get_text(strip=True))
        
        # Extraer referencia del contenedor
        ref_tag = contenedor.find('span', class_='contRef')
        if ref_tag:
            ref_text = ref_tag.get_text(strip=True)
            if 'Ref. ' in ref_text:
                referencia = ref_text.replace('Ref. ', '').replace('-', '').strip()
        
        # Extraer operación de la URL
        url_parts = url_inmueble.split('/')
        if len(url_parts) > 4:
            operacion_raw = url_parts[4].replace('_', ' ')
            if 'lloguer' in operacion_raw:
                operacion = 'Alquiler'
            elif 'venda' in operacion_raw:
                operacion = 'Venta'
            else:
                operacion = limpiar_texto(operacion_raw).title()
        
        # Extraer población de la dirección en el contenedor
        direccion_div = contenedor.find('div', class_='direccion')
        if direccion_div:
            poblacion = limpiar_texto(direccion_div.get_text(strip=True))
        
        # Extraer precio del contenedor
        precio_div = contenedor.find('div', class_='precio')
        if precio_div:
            precio_span = precio_div.find('span')
            if precio_span:
                precio_text = precio_span.get_text(strip=True)
                precio = extraer_precio(precio_text)
        
        # Extraer características del contenedor
        caract_div = contenedor.find('div', class_='contCaract')
        if caract_div:
            # Buscar superficie
            superficie_li = caract_div.find('li')
            if superficie_li:
                superficie_text = superficie_li.get_text(strip=True)
                superficie_match = re.search(r'(\d+)\s*m', superficie_text)
                if superficie_match:
                    superficie = int(superficie_match.group(1))
            
            # Buscar habitaciones y baños en el texto
            caract_text = caract_div.get_text(strip=True)
            
            # Buscar habitaciones
            hab_match = re.search(r'(\d+)\s*hab', caract_text, re.IGNORECASE)
            if hab_match:
                habitaciones = int(hab_match.group(1))
            
            # Buscar baños
            baño_match = re.search(r'(\d+)\s*baño', caract_text, re.IGNORECASE)
            if baño_match:
                baños = int(baño_match.group(1))
        
        return {
            'reference': referencia,
            'operation': operacion,
            'price': precio,
            'rooms': habitaciones,
            'bathrooms': baños,
            'surface': superficie,
            'title': titulo,
            'location': poblacion,
            'address': 'N/A',
            'url': url_inmueble,
            'website': self.website
        }


if __name__ == "__main__":
    scraper = FinquesmarquesScraper()
    scraper.run()