import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import unicodedata
from ..database.operations import PropertyRepository
from ..database.connection import create_tables
from ..utils.text_cleaner import limpiar_texto, extraer_precio, detectar_pas_de_la_casa, detectar_arinsal, detectar_bordes, convertir_a_entero

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
        
        # NUEVA LÓGICA: Verificar descripción para ubicaciones específicas
        
        # Verificar Pas de la Casa (Encamp o ubicaciones genéricas)
        if poblacion and ('encamp' in poblacion.lower() or 'andorra' in poblacion.lower() or poblacion == 'N/A'):
            print(f"🔍 [FINQUESMARQUES] Verificando descripción para posible Pas de la Casa: {url_inmueble}")
            descripcion = self.get_property_description(url_inmueble)
            
            if descripcion and detectar_pas_de_la_casa(descripcion):
                print(f"✅ [FINQUESMARQUES] ¡Detectado Pas de la Casa en descripción! Cambiando ubicación de '{poblacion}' a 'Pas de la Casa'")
                poblacion = "Pas de la Casa"
            else:
                print(f"❌ [FINQUESMARQUES] No se detectó Pas de la Casa en la descripción")
        
        # Verificar Arinsal (La Massana o Arinsal directo)
        elif poblacion and ('massana' in poblacion.lower() or 'arinsal' in poblacion.lower()):
            print(f"🔍 [FINQUESMARQUES] Verificando descripción para posible Arinsal: {url_inmueble}")
            descripcion = self.get_property_description(url_inmueble)
            
            if descripcion and detectar_arinsal(descripcion):
                print(f"✅ [FINQUESMARQUES] ¡Detectado Arinsal en descripción! Cambiando ubicación de '{poblacion}' a 'Arinsal'")
                poblacion = "Arinsal"
            else:
                print(f"❌ [FINQUESMARQUES] No se detectó Arinsal en la descripción")
        
        # Verificar Bordes d'Envalira (Canillo, Soldeu, etc.)
        elif poblacion and ('canillo' in poblacion.lower() or 'soldeu' in poblacion.lower() or 
                           'incles' in poblacion.lower() or 'tarter' in poblacion.lower() or
                           'bordes' in poblacion.lower()):
            print(f"🔍 [FINQUESMARQUES] Verificando descripción para posible Bordes d'Envalira: {url_inmueble}")
            descripcion = self.get_property_description(url_inmueble)
            
            if descripcion and detectar_bordes(descripcion):
                print(f"✅ [FINQUESMARQUES] ¡Detectado Bordes d'Envalira en descripción! Cambiando ubicación de '{poblacion}' a 'Bordes d\\'Envalira'")
                poblacion = "Bordes d'Envalira"
            else:
                print(f"❌ [FINQUESMARQUES] No se detectó Bordes d'Envalira en la descripción")
        else:
            print(f"ℹ️ [FINQUESMARQUES] Población '{poblacion}' no necesita verificación")
        
        # Extraer precio del contenedor
        precio_div = contenedor.find('div', class_='precio')
        if precio_div:
            precio_span = precio_div.find('span')
            if precio_span:
                precio_text = precio_span.get_text(strip=True)
                precio = extraer_precio(precio_text)
        
        # FILTRO: Saltar propiedades con precio mayor a 450,000€
        if precio > 450000:
            print(f"⚠️ [FINQUESMARQUES] Propiedad filtrada por precio alto: {precio:,.0f}€ > 450,000€")
            return None
        
        # Extraer características del contenedor - BUSCAR EN UL.LIST-INLINE
        caract_ul = contenedor.find('ul', class_='list-inline')
        if caract_ul:
            li_elements = caract_ul.find_all('li')
            
            for li in li_elements:
                li_text = li.get_text(strip=True)
                
                # Buscar habitaciones (en catalán: "Habs")
                hab_match = re.search(r'(\d+)\s*habs?', li_text, re.IGNORECASE)
                if hab_match:
                    habitaciones = int(hab_match.group(1))
                
                # Buscar baños (en catalán: "Banys")
                bany_match = re.search(r'(\d+)\s*banys?', li_text, re.IGNORECASE)
                if bany_match:
                    baños = int(bany_match.group(1))
                
                # Buscar superficie (m² o m2)
                superficie_match = re.search(r'(\d+(?:[.,]\d+)?)\s*m', li_text, re.IGNORECASE)
                if superficie_match:
                    superficie_str = superficie_match.group(1).replace(',', '.')
                    superficie = float(superficie_str)
        
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