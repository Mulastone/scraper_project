import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from ..database.operations import PropertyRepository
from ..database.connection import create_tables
from ..utils.text_cleaner import limpiar_texto, extraer_precio, detectar_pas_de_la_casa, detectar_arinsal, detectar_bordes

class NouaireScraper:
    def __init__(self):
        self.base_url = "https://www.nouaire.com"
        self.website = "www.nouaire.com"
        
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
    
    def detect_special_locations(self, poblacion, url_inmueble):
        """
        Detecta poblaciones especiales de Andorra basándose en la descripción
        """
        if not poblacion:
            return poblacion
            
        # Si la población inicial es Encamp, verificar si realmente es Pas de la Casa
        if 'encamp' in poblacion.lower() or poblacion == 'N/A':
            print(f"🔍 Verificando descripción para posible Pas de la Casa: {url_inmueble}")
            descripcion = self.get_property_description(url_inmueble)
            
            if descripcion and detectar_pas_de_la_casa(descripcion):
                print(f"✅ ¡Detectado Pas de la Casa en descripción! Cambiando ubicación de '{poblacion}' a 'Pas de la Casa'")
                return "Pas de la Casa"
            else:
                print(f"❌ No se detectó Pas de la Casa en la descripción")
        
        # Verificar si es Arinsal (independiente de la población inicial)
        elif 'massana' in poblacion.lower():
            print(f"🔍 Verificando descripción para posible Arinsal: {url_inmueble}")
            descripcion = self.get_property_description(url_inmueble)
            
            if descripcion and detectar_arinsal(descripcion):
                print(f"✅ ¡Detectado Arinsal en descripción! Cambiando ubicación de '{poblacion}' a 'Arinsal'")
                return "Arinsal"
            else:
                print(f"❌ No se detectó Arinsal en la descripción")
        
        # Verificar si es Bordes d'Envalira
        elif 'canillo' in poblacion.lower() or 'soldeu' in poblacion.lower():
            print(f"🔍 Verificando descripción para posible Bordes d'Envalira: {url_inmueble}")
            descripcion = self.get_property_description(url_inmueble)
            
            if descripcion and detectar_bordes(descripcion):
                print(f"✅ ¡Detectado Bordes d'Envalira en descripción! Cambiando ubicación de '{poblacion}' a 'Bordes d\\'Envalira'")
                return "Bordes d'Envalira"
            else:
                print(f"❌ No se detectó Bordes d'Envalira en la descripción")
        else:
            print(f"ℹ️ Población '{poblacion}' no necesita verificación")
            
        return poblacion
        
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
            all_properties = []  # Lista para acumular todas las propiedades
            
            # Iterar sobre todas las páginas
            for page_num in range(1, last_page_number + 1):
                url = f"{self.base_url}/prop/buscador/limit:100/page:{page_num}"
                print(f"Procesando página {page_num}: {url}")
                
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    propiedades = soup.find_all('div', class_='row pt10 pb10')
                    
                    # Extraer datos de propiedades (sin guardar aún)
                    for propiedad in propiedades:
                        try:
                            property_data = self.extract_property_data(propiedad, urls_unicas)
                            if property_data:
                                all_properties.append(property_data)
                                
                        except Exception as e:
                            print(f"Error al procesar una propiedad: {e}")
                            continue
                            
                except Exception as e:
                    print(f"Error al procesar página {page_num}: {e}")
                    continue
            
            # Guardar todas las propiedades en lote al final
            if all_properties:
                saved_count = PropertyRepository.save_properties_batch(all_properties)
                print(f"Scraping completado. Procesadas {len(urls_unicas)} propiedades únicas, {saved_count} guardadas.")
            else:
                print("Scraping completado. No se encontraron propiedades válidas.")
                    
        except Exception as e:
            print(f"Error en el scraper: {e}")
    
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
            
            # Buscar en div de descripción (común en nouaire)
            desc_div = soup.find('div', string=re.compile(r'Descripción', re.IGNORECASE))
            if desc_div:
                # Buscar el contenido siguiente
                parent = desc_div.parent
                if parent:
                    desc_content = parent.find_next_sibling()
                    if desc_content:
                        descripcion = desc_content.get_text(strip=True)
            
            # Si no se encontró, buscar por otros selectores comunes
            if not descripcion:
                # Buscar en párrafos largos (probable descripción)
                paragrafos = soup.find_all('p')
                for p in paragrafos:
                    texto = p.get_text(strip=True)
                    if len(texto) > 100:  # Párrafos largos probablemente sean descripción
                        descripcion += " " + texto
            
            # También buscar en divs que contengan mucho texto
            if not descripcion:
                divs = soup.find_all('div')
                for div in divs:
                    texto = div.get_text(strip=True)
                    if len(texto) > 200 and 'ubicación' in texto.lower():
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
                superficie_match = re.search(r'(\d+(?:[.,]\d+)?)m', superficie_text)
                if superficie_match:
                    superficie_str = superficie_match.group(1).replace(',', '.')
                    superficie = float(superficie_str)
            
            # Extraer precio
            precio_div = propiedad.find('div', class_='col-xs-6 col-sm-1 text-right')
            if precio_div:
                precio_text = precio_div.get_text(strip=True)
                precio = extraer_precio(precio_text)
            
            # FILTRO 1: Saltar propiedades con precio mayor a 450,000€
            if precio > 450000:
                print(f"⚠️ Propiedad filtrada por precio alto: {precio:,.0f}€ > 450,000€")
                return None
            
            # FILTRO 2: Verificar que la propiedad esté en Andorra ANTES de detectar poblaciones especiales
            if not self.is_andorra_location(poblacion):
                print(f"🌍 Propiedad filtrada por estar fuera de Andorra: {poblacion}")
                return None
                
            # FILTRO 3: Detectar poblaciones especiales DESPUÉS de confirmar que está en Andorra
            poblacion = self.detect_special_locations(poblacion, url_inmueble)
            
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

if __name__ == "__main__":
    scraper = NouaireScraper()
    scraper.run()