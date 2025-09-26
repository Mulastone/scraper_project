import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from ..database.operations import PropertyRepository
from ..database.connection import create_tables
from ..utils.text_cleaner import limpiar_texto, extraer_precio

class NouaireScraper:
    def __init__(self):
        self.base_url = "https://www.nouaire.com"
        self.website = "www.nouaire.com"
        
    def run(self):
        """
        Ejecuta el scraper principal
        """
        # Crear tablas si no existen
        create_tables()
        
        try:
            # Obtener número de propiedades y páginas
            last_page_number = self.get_last_page_number()
            
            urls_unicas = set()
            
            # Iterar sobre todas las páginas
            for page_num in range(1, last_page_number + 1):
                url = f"{self.base_url}/prop/buscador/limit:100/page:{page_num}"
                print(f"Procesando página {page_num}: {url}")
                
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    propiedades = soup.find_all('div', class_='row pt10 pb10')
                    
                    for propiedad in propiedades:
                        try:
                            property_data = self.extract_property_data(propiedad, urls_unicas)
                            if property_data:
                                PropertyRepository.save_property(property_data)
                                
                        except Exception as e:
                            print(f"Error al procesar una propiedad: {e}")
                            continue
                            
                except Exception as e:
                    print(f"Error al procesar página {page_num}: {e}")
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
            propiedades = soup.find_all('div', class_='row pt10 pb10')
            
            urls_unicas = set()
            scraped_data = []
            
            for propiedad in propiedades:
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
    
    def get_last_page_number(self):
        """
        Obtiene el número de la última página basado en el número de propiedades
        """
        try:
            url_base = f"{self.base_url}/prop/comprar"
            response = requests.get(url_base)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar el icono de building para obtener el número de propiedades
            icono_building = soup.find('i', class_='fa fa-building')
            numero_propiedades = 0
            
            if icono_building:
                span_propiedades = icono_building.find_next('span')
                if span_propiedades:
                    texto_span = span_propiedades.get_text(strip=True)
                    resultado = re.search(r'\d+', texto_span)
                    if resultado:
                        numero_propiedades = int(resultado.group())
            
            # Calcular páginas (100 propiedades por página)
            return max(1, int(numero_propiedades / 100)) if numero_propiedades else 1
            
        except Exception as e:
            print(f"Error al obtener número de páginas: {e}")
            return 1
    
    def extract_property_data(self, propiedad, urls_unicas):
        """
        Extrae los datos de una propiedad
        """
        # Inicializar variables
        titulo = referencia = operacion = poblacion = 'N/A'
        precio = habitaciones = baños = superficie = 0
        url_inmueble = 'N/A'
        
        try:
            # Extraer URL (primer enlace encontrado)
            enlace = propiedad.find('a', href=True)
            if enlace:
                url_inmueble = f"{self.base_url}{enlace['href']}"
                
                if url_inmueble in urls_unicas:
                    return None
                    
                urls_unicas.add(url_inmueble)
            else:
                return None
            
            # Extraer referencia (segundo div con enlace)
            ref_div = propiedad.find('div', class_='col-xs-12 col-sm-2 hidden-xs')
            if ref_div:
                ref_link = ref_div.find('a')
                if ref_link:
                    referencia = ref_link.get_text(strip=True)
            
            # Extraer operación (del icono con título o del texto visible en móvil)
            # Primero intentar con el icono
            operacion_icon = propiedad.find('i', class_='fa fa-square')
            if operacion_icon:
                operacion_title = operacion_icon.get('title', '')
                if operacion_title:
                    operacion = operacion_title
            
            # Si no se encontró, buscar en el texto visible para móviles
            if operacion == 'N/A':
                mobile_div = propiedad.find('div', class_='col-xs-12 visible-xs-inline')
                if mobile_div:
                    operacion_span = mobile_div.find('span')
                    if operacion_span:
                        operacion = operacion_span.get_text(strip=True)
            
            # Extraer tipo de propiedad
            tipo_div = propiedad.find('div', class_='col-xs-4 col-sm-2 hidden-xs')
            if tipo_div:
                titulo = limpiar_texto(tipo_div.get_text(strip=True))
            
            # Si no se encontró título en desktop, buscarlo en móvil
            if titulo == 'N/A':
                mobile_title = propiedad.find('div', class_='col-xs-12 visible-xs-inline')
                if mobile_title:
                    title_link = mobile_title.find('a')
                    if title_link:
                        title_text = title_link.get_text(strip=True)
                        # Extraer solo el tipo (después de la operación)
                        if ' ' in title_text:
                            parts = title_text.split(' ', 1)
                            if len(parts) > 1:
                                titulo = parts[1].split(' en ')[0]  # "Apartamento en Ordino" -> "Apartamento"
            
            # Extraer población
            poblacion_div = propiedad.find('div', class_='col-xs-8 col-sm-2 hidden-xs')
            if poblacion_div:
                poblacion = limpiar_texto(poblacion_div.get_text(strip=True))
            
            # Si no se encontró población en desktop, extraerla del título móvil
            if poblacion == 'N/A':
                mobile_title = propiedad.find('div', class_='col-xs-12 visible-xs-inline')
                if mobile_title:
                    title_link = mobile_title.find('a')
                    if title_link:
                        title_text = title_link.get_text(strip=True)
                        if ' en ' in title_text:
                            poblacion = title_text.split(' en ')[-1]
            
            # Extraer superficie
            superficie_div = propiedad.find('div', class_='col-xs-6 col-sm-1')
            if superficie_div:
                superficie_text = superficie_div.get_text(strip=True)
                superficie_match = re.search(r'(\d+)m', superficie_text)
                if superficie_match:
                    superficie = int(superficie_match.group(1))
            
            # Extraer precio
            precio_div = propiedad.find('div', class_='col-xs-6 col-sm-1 text-right')
            if precio_div:
                precio_text = precio_div.get_text(strip=True)
                precio = extraer_precio(precio_text)
            
            # Extraer habitaciones (div con icono fa-bed visible-xs-inline)
            habitaciones_divs = propiedad.find_all('div', class_='col-xs-6 col-sm-1 strong text-right')
            for div in habitaciones_divs:
                bed_icon = div.find('i', class_='fa fa-bed visible-xs-inline')
                if bed_icon:
                    # Es el div de habitaciones
                    habitaciones_text = div.get_text(strip=True)
                    habitaciones_match = re.search(r'(\d+)', habitaciones_text)
                    if habitaciones_match:
                        habitaciones = int(habitaciones_match.group(1))
                    break
            
            # Extraer baños (div con icono fa-bath visible-xs-inline)
            for div in habitaciones_divs:  # Reutilizar la misma búsqueda
                bath_icon = div.find('i', class_='fa fa-bath visible-xs-inline')
                if bath_icon:
                    # Es el div de baños
                    baños_text = div.get_text(strip=True)
                    baños_match = re.search(r'(\d+)', baños_text)
                    if baños_match:
                        baños = int(baños_match.group(1))
                    break
            
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
            
        except Exception as e:
            print(f"Error al extraer datos de propiedad: {e}")
            return None
    
    def convertir_a_entero(self, valor):
        """Convierte un valor a entero, retorna 0 si no es posible"""
        try:
            # Extraer solo números del texto
            numeros = re.findall(r'\d+', str(valor))
            return int(numeros[0]) if numeros else 0
        except (ValueError, IndexError):
            return 0
    
    def convertir_a_entero_limpiar(self, valor):
        """Convierte un valor a entero removiendo texto como 'm2', 'm²'"""
        try:
            # Remover texto común de superficie
            valor_limpio = str(valor).replace('m2', '').replace('m²', '').replace('m', '').strip()
            numeros = re.findall(r'\d+', valor_limpio)
            return int(numeros[0]) if numeros else 0
        except (ValueError, IndexError):
            return 0
    
    def modificar_operacion(self, operacion):
        """Modifica y limpia el texto de operación"""
        operacion = operacion.lower()
        if 'venta' in operacion or 'vendre' in operacion:
            return 'Venta'
        elif 'alquiler' in operacion or 'lloguer' in operacion:
            return 'Alquiler'
        return limpiar_texto(operacion).title()