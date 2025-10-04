"""
Scraper for Expofinques real estate website
URL: http://www.expofinques.com/es/venta
"""

import requests
from bs4 import BeautifulSoup
import re
from ..database.operations import PropertyRepository
from ..models.property import Property
from ..utils.text_cleaner import limpiar_texto, extraer_precio, detectar_pas_de_la_casa, detectar_arinsal, detectar_bordes, convertir_a_entero


class ExpofinquesScraper:
    def __init__(self):
        self.base_url = "http://www.expofinques.com"
        self.search_url = "http://www.expofinques.com/es/venta"
        
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
    
    def scrape_properties(self):
        """Scrape properties from Expofinques"""
        print(f"🕷️ Scraping Expofinques: {self.search_url}")
        
        try:
            response = requests.get(self.search_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the main properties table
            table = soup.find('table', id='infoListado')
            
            if not table:
                print("❌ No se encontró la tabla de propiedades")
                return []
            
            tbody = table.find('tbody')
            if not tbody:
                print("❌ No se encontró el cuerpo de la tabla")
                return []
            
            rows = tbody.find_all('tr')
            print(f"✅ Encontradas {len(rows)} propiedades")
            
            properties = []
            
            for row in rows:
                property_data = self.extract_property_data(row)
                if property_data:
                    properties.append(property_data)
            
            print(f"✅ Scrapeadas {len(properties)} propiedades exitosamente")
            return properties
            
        except Exception as e:
            print(f"❌ Error scraping Expofinques: {e}")
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
    
    def extract_property_data(self, row):
        """Extract property data from a table row"""
        try:
            cells = row.find_all('td')
            
            if len(cells) < 20:
                return None
            
            # URL from first cell link
            url = ""
            link_element = cells[0].find('a')
            if link_element and link_element.get('href'):
                url = self.base_url + link_element['href']
            
            # Reference from cell 2
            reference = limpiar_texto(cells[2].get_text())
            
            # Property type from cell 3
            property_type = limpiar_texto(cells[3].get_text())
            
            # Location from cell 4
            location = limpiar_texto(cells[4].get_text())
            
            # NUEVA LÓGICA: Verificar descripción para ubicaciones específicas
            
            # Verificar Pas de la Casa (Encamp o ubicaciones genéricas)
            if location and ('encamp' in location.lower() or 'andorra' in location.lower() or location == 'N/A'):
                print(f"🔍 [EXPOFINQUES] Verificando descripción para posible Pas de la Casa: {url}")
                descripcion = self.get_property_description(url)
                
                if descripcion and detectar_pas_de_la_casa(descripcion):
                    print(f"✅ [EXPOFINQUES] ¡Detectado Pas de la Casa en descripción! Cambiando ubicación de '{location}' a 'Pas de la Casa'")
                    location = "Pas de la Casa"
                else:
                    print(f"❌ [EXPOFINQUES] No se detectó Pas de la Casa en la descripción")
            
            # Verificar Arinsal (La Massana o Arinsal directo)
            elif location and ('massana' in location.lower() or 'arinsal' in location.lower()):
                print(f"🔍 [EXPOFINQUES] Verificando descripción para posible Arinsal: {url}")
                descripcion = self.get_property_description(url)
                
                if descripcion and detectar_arinsal(descripcion):
                    print(f"✅ [EXPOFINQUES] ¡Detectado Arinsal en descripción! Cambiando ubicación de '{location}' a 'Arinsal'")
                    location = "Arinsal"
                else:
                    print(f"❌ [EXPOFINQUES] No se detectó Arinsal en la descripción")
            
            # Verificar Bordes d'Envalira (Canillo, Soldeu, etc.)
            elif location and ('canillo' in location.lower() or 'soldeu' in location.lower() or 
                             'incles' in location.lower() or 'tarter' in location.lower() or
                             'bordes' in location.lower()):
                print(f"🔍 [EXPOFINQUES] Verificando descripción para posible Bordes d'Envalira: {url}")
                descripcion = self.get_property_description(url)
                
                if descripcion and detectar_bordes(descripcion):
                    print(f"✅ [EXPOFINQUES] ¡Detectado Bordes d'Envalira en descripción! Cambiando ubicación de '{location}' a 'Bordes d\\'Envalira'")
                    location = "Bordes d'Envalira"
                else:
                    print(f"❌ [EXPOFINQUES] No se detectó Bordes d'Envalira en la descripción")
            else:
                print(f"ℹ️ [EXPOFINQUES] Ubicación '{location}' no necesita verificación")
            
            # Price from cell 5
            price_text = cells[5].get_text()
            price = extraer_precio(price_text)
            
            # FILTRO 1: Saltar propiedades con precio mayor a 450,000€
            if price > 450000:
                print(f"⚠️ [EXPOFINQUES] Propiedad filtrada por precio alto: {price:,.0f}€ > 450,000€")
                return None
            
            # FILTRO 2: Verificar que la propiedad esté en Andorra ANTES de detectar poblaciones especiales
            if not self.is_andorra_location(location):
                print(f"🌍 [EXPOFINQUES] Propiedad filtrada por estar fuera de Andorra: {location}")
                return None
            
            # Surface from cell 6
            surface_text = cells[6].get_text()
            surface = convertir_a_entero(surface_text)
            
            # Bedrooms from cell 7
            bedrooms_text = cells[7].get_text()
            bedrooms = convertir_a_entero(bedrooms_text) if bedrooms_text.strip() else None
            
            # Bathrooms from cell 8
            bathrooms_text = cells[8].get_text()
            bathrooms = convertir_a_entero(bathrooms_text) if bathrooms_text.strip() else None
            
            # Description from cell 15
            description = limpiar_texto(cells[15].get_text()) if len(cells) > 15 else ""
            
            # Title from cell 18
            title = limpiar_texto(cells[18].get_text()) if len(cells) > 18 else ""
            
            # Use title as main title, fallback to description or property type
            if not title:
                title = description[:100] + "..." if len(description) > 100 else description
            if not title:
                title = f"{property_type} en {location}"
            
            # Image URL from first cell
            image_url = ""
            img_element = cells[0].find('img')
            if img_element and img_element.get('src'):
                img_src = img_element['src']
                if img_src.startswith('/'):
                    image_url = self.base_url + img_src
                else:
                    image_url = img_src
            
            # Create Property object - only using fields that exist in the model
            property_obj = Property(
                reference=reference,
                operation='venta',
                price=price,
                rooms=bedrooms,
                bathrooms=bathrooms,
                surface=surface,
                title=title,
                location=location,
                address=location,  # Use location as address
                url=url,
                website='expofinques'
            )
            
            return property_obj
            
        except Exception as e:
            print(f"❌ Error extracting property data: {e}")
            return None
    
    def save_to_database(self, properties):
        """Save properties to database"""
        if not properties:
            print("⚠️ No hay propiedades para guardar")
            return
        
        try:
            saved_count = 0
            for property_obj in properties:
                # Convert Property object to dictionary
                property_data = {
                    'reference': property_obj.reference,
                    'operation': property_obj.operation,
                    'price': property_obj.price,
                    'rooms': property_obj.rooms,
                    'bathrooms': property_obj.bathrooms,
                    'surface': property_obj.surface,
                    'title': property_obj.title,
                    'location': property_obj.location,
                    'address': property_obj.address,
                    'url': property_obj.url,
                    'website': property_obj.website
                }
                
                if PropertyRepository.save_property(property_data):
                    saved_count += 1
            
            print(f"✅ Guardadas {saved_count} propiedades en la base de datos")
            
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
    
    def run(self):
        """Run the complete scraping process"""
        print("🚀 Iniciando scraper de Expofinques...")
        
        # Scrape properties
        properties = self.scrape_properties()
        
        if properties:
            # Save to database
            self.save_to_database(properties)
            print(f"✅ Proceso completado: {len(properties)} propiedades procesadas")
        else:
            print("❌ No se encontraron propiedades")


if __name__ == "__main__":
    scraper = ExpofinquesScraper()
    scraper.run()
