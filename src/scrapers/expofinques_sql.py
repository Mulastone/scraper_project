"""
Scraper for Expofinques real estate website
URL: http://www.expofinques.com/es/venta
"""

import requests
from bs4 import BeautifulSoup
import re
from ..database.operations import PropertyRepository
from ..models.property import Property
from ..utils.text_cleaner import limpiar_texto, extraer_precio, convertir_a_entero


class ExpofinquesScraper:
    def __init__(self):
        self.base_url = "http://www.expofinques.com"
        self.search_url = "http://www.expofinques.com/es/venta"
    
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
            
            # Price from cell 5
            price_text = cells[5].get_text()
            price = extraer_precio(price_text)
            
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
