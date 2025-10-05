#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper para pisos.com - Propiedades en Andorra
===============================================

Este módulo extrae propiedades inmobiliarias de pisos.com
limitadas a Andorra con precio máximo de 450.000€.

Estructura del sitio:
- URL base: https://www.pisos.com/venta/pisos-andorra/hasta-400000/
- Propiedades individuales: /comprar/[tipo]-[ubicacion]-[id]/
- Paginación: /venta/pisos-andorra/hasta-400000/[numero]/

Autores: Axel Rasmussen
Fecha: Octubre 2025
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import urljoin, urlparse
import logging
from datetime import datetime
from ..database.operations import PropertyRepository
from ..database.connection import create_tables
from ..utils.text_cleaner import limpiar_texto

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PisoscomScraper:
    def __init__(self):
        self.base_url = "https://www.pisos.com"
        self.search_url = "https://www.pisos.com/venta/pisos-andorra/hasta-400000/"
        self.website = "pisos.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Ubicaciones válidas de Andorra
        self.andorra_keywords = [
            'andorra', 'escaldes', 'engordany', 'sant julia', 'sant julià', 'encamp', 'canillo', 
            'massana', 'la massana', 'ordino', 'pas de la casa', 'arinsal', 'bordes', 'envalira',
            'tarter', 'el tarter', 'soldeu', 'incles', 'pal', 'serrat', 'el serrat', 'les bons', 
            'santa coloma', 'erts', 'llorts', 'sispony', 'ransol', 'aixovall', 'nagol',
            'bixessarri', 'aixàs', 'meritxell', 'vila', 'anyós', 'els cortals', 'centre',
            'andorra la vella', 'escaldes engordany', 'la massana centro urbano', 'encamp centro urbano',
            'canillo centro urbano', 'pas_de_la_casa', 'santa_coloma_distrito', 'andorra_la_vella_centre',
            'escaldes_engordany_centro_urbano', 'la_massana_centro_urbano', 'encamp_centro_urbano',
            'canillo_centro_urbano'
        ]
        
    def extract_number(self, text):
        """Extrae números de un texto, preservando decimales."""
        if not text:
            return None
        # Buscar números con posibles puntos y comas
        numbers = re.findall(r'[\d.,]+', str(text))
        if not numbers:
            return None
        
        # Tomar el primer número encontrado
        number_str = numbers[0]
        # Limpiar formato europeo (punto como separador de miles, coma como decimal)
        number_str = number_str.replace('.', '').replace(',', '.')
        
        try:
            return float(number_str)
        except ValueError:
            return None

    def clean_text(self, text):
        """Limpia y normaliza texto."""
        if not text:
            return ""
        # Limpiar espacios y caracteres especiales
        cleaned = re.sub(r'\s+', ' ', str(text).strip())
        return cleaned

    def is_andorra_location(self, location_text):
        """
        Verifica si la ubicación corresponde a Andorra.
        
        Args:
            location_text (str): Texto de ubicación a verificar
            
        Returns:
            bool: True si es ubicación de Andorra, False si no
        """
        if not location_text:
            return False
            
        location_text = location_text.lower()
        
        # Verificar si alguna palabra clave está presente
        for keyword in self.andorra_keywords:
            if keyword in location_text:
                return True
                
        return False

    def extract_property_from_detail_page(self, url):
        """Extrae datos completos de la página de detalle de una propiedad."""
        try:
            logger.info(f"Extrayendo detalles de: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Título de la propiedad
            title_elem = (soup.find('h1') or 
                         soup.find('title') or
                         soup.find('h2', class_=re.compile(r'title|heading')))
            title = self.clean_text(title_elem.get_text()) if title_elem else "Propiedad en Andorra"
            
            # Precio - buscar más agresivamente
            price_elem = (soup.find('span', class_=re.compile(r'price')) or
                         soup.find('div', class_=re.compile(r'price')) or
                         soup.find('strong', text=re.compile(r'\d+\.?\d*\s*€')) or
                         soup.find(text=re.compile(r'\d{3,6}\.?\d*\s*€')))
            
            price = None
            if price_elem:
                if hasattr(price_elem, 'get_text'):
                    price_text = price_elem.get_text()
                else:
                    price_text = str(price_elem)
                price = self.extract_number(price_text)
                logger.info(f"Precio encontrado: {price}")
            
            if not price or price > 450000:
                logger.info(f"Propiedad descartada por precio: {price}")
                return None
            
            # Ubicación - buscar más agresivamente
            location = "Andorra"
            
            # Primero intentar extraer de la URL que suele contener la ubicación
            url_parts = url.split('-')
            for part in url_parts:
                if self.is_andorra_location(part):
                    location = part.replace('_', ' ').title()
                    logger.info(f"Ubicación extraída de URL: {location}")
                    break
            
            # Si no encontramos en URL, buscar en el HTML
            if location == "Andorra":
                location_elem = (soup.find('span', class_=re.compile(r'location|address|zona')) or
                               soup.find('div', class_=re.compile(r'location|address|zona')) or
                               soup.find('p', class_=re.compile(r'location|address|zona')) or
                               soup.find('h2', text=re.compile(r'[Cc]anillo|[Ee]ncamp|[Aa]ndorra|[Mm]assana|[Ee]scaldes|[Ss]oldeu')) or
                               soup.find(text=re.compile(r'[Cc]anillo|[Ee]ncamp|[Aa]ndorra|[Mm]assana|[Ee]scaldes|[Ss]oldeu')))
                
                if location_elem:
                    if hasattr(location_elem, 'get_text'):
                        location_text = location_elem.get_text()
                    else:
                        location_text = str(location_elem)
                    
                    # Filtrar textos genéricos
                    if "cerca de mi ubicación" not in location_text.lower():
                        potential_location = self.clean_text(location_text)
                        if self.is_andorra_location(potential_location):
                            location = potential_location
                            logger.info(f"Ubicación extraída de HTML: {location}")
            
            # Verificar que la ubicación final sea válida
            if not self.is_andorra_location(location):
                logger.info(f"Propiedad descartada por ubicación: {location}")
                return None
            
            # Habitaciones, baños, metros cuadrados - buscar más agresivamente
            rooms = 0
            bathrooms = 0
            square_meters = 0
            
            # Buscar datos en todo el HTML
            all_text = soup.get_text()
            
            # Habitaciones
            room_matches = re.findall(r'(\d+)\s*(?:hab|habitacion|dormitor)', all_text, re.IGNORECASE)
            if room_matches:
                rooms = int(room_matches[0])
            
            # Baños
            bath_matches = re.findall(r'(\d+)\s*baño', all_text, re.IGNORECASE)
            if bath_matches:
                bathrooms = int(bath_matches[0])
            
            # Metros cuadrados
            sqm_matches = re.findall(r'(\d+)\s*m[²2]', all_text, re.IGNORECASE)
            if sqm_matches:
                square_meters = int(sqm_matches[0])
            
            # Descripción - buscar en varios elementos
            desc_elem = (soup.find('div', class_=re.compile(r'description|content|detail|resumen')) or
                        soup.find('p', class_=re.compile(r'description|content|detail|resumen')) or
                        soup.find('section', class_=re.compile(r'description|content|detail')))
            
            if desc_elem:
                description = limpiar_texto(desc_elem.get_text()[:300])
            else:
                # Buscar párrafos largos que puedan ser descripción
                paragraphs = soup.find_all('p')
                long_paragraphs = [p.get_text() for p in paragraphs if len(p.get_text()) > 50]
                if long_paragraphs:
                    description = limpiar_texto(long_paragraphs[0][:300])
                else:
                    description = f"Propiedad en {location}"
            
            # Imagen
            img_elem = soup.find('img', src=True)
            image_url = ""
            if img_elem and img_elem['src']:
                image_url = urljoin(self.base_url, img_elem['src'])
            
            property_data = {
                'title': title,
                'price': price,
                'location': location,
                'rooms': rooms,
                'bathrooms': bathrooms,
                'square_meters': square_meters,
                'description': description,
                'url': url,
                'image_url': image_url,
                'source': self.website,
                'scraped_at': datetime.now()
            }
            
            logger.info(f"✓ Propiedad extraída: €{price:,} - {title[:50]}...")
            return property_data
            
        except Exception as e:
            logger.error(f"Error extrayendo detalles de {url}: {e}")
            return None

    def extract_property_details(self, property_card):
        """Extrae los detalles de una propiedad del HTML del card."""
        try:
            # URL de la propiedad
            link_elem = property_card.find('a', href=True)
            if not link_elem or not link_elem['href']:
                return None
            
            property_url = urljoin(self.base_url, link_elem['href'])
            
            # Extraer datos básicos del card
            title = self.clean_text(link_elem.get_text()) if link_elem.get_text() else "Propiedad"
            
            # Precio del card
            price_elem = property_card.find(text=re.compile(r'\d+.*€'))
            price = None
            if price_elem:
                price = self.extract_number(price_elem)
                if not price or price > 450000:
                    return None
            
            # Ubicación del card
            location_elem = property_card.find(text=re.compile(r'[Cc]anillo|[Ee]ncamp|[Aa]ndorra|[Mm]assana|[Ee]scaldes'))
            location = "Andorra"
            if location_elem:
                location = self.clean_text(str(location_elem))
                if not self.is_andorra_location(location):
                    return None
            
            # Si no encontramos precio en el card, intentar obtener datos completos de la página de detalle
            if not price:
                return self.extract_property_from_detail_page(property_url)
            
            # Habitaciones, baños, metros del card
            rooms = 0
            bathrooms = 0
            square_meters = 0
            
            characteristics = property_card.find_all(text=re.compile(r'\d+\s*(hab|baño|m²)'))
            for char in characteristics:
                char_text = str(char).lower()
                if 'hab' in char_text:
                    rooms = int(self.extract_number(char_text) or 0)
                elif 'baño' in char_text:
                    bathrooms = int(self.extract_number(char_text) or 0)
                elif 'm²' in char_text:
                    square_meters = int(self.extract_number(char_text) or 0)
            
            # Descripción básica
            description = f"Propiedad en {location}"
            
            # Imagen
            img_elem = property_card.find('img', src=True)
            image_url = ""
            if img_elem and img_elem['src']:
                image_url = urljoin(self.base_url, img_elem['src'])
            
            return {
                'title': title,
                'price': price,
                'location': location,
                'rooms': rooms,
                'bathrooms': bathrooms,
                'square_meters': square_meters,
                'description': description,
                'url': property_url,
                'image_url': image_url,
                'source': self.website,
                'scraped_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo detalles de propiedad: {e}")
            return None

    def scrape_page(self, url):
        """Extrae propiedades de una página específica."""
        try:
            logger.info(f"Scrapeando página: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            properties = []
            
            # Buscar enlaces que apunten a /comprar/ (propiedades individuales)
            comprar_links = soup.find_all('a', href=re.compile(r'/comprar/'))
            
            logger.info(f"Encontrados {len(comprar_links)} enlaces de propiedades")
            
            for link in comprar_links:
                try:
                    # Extraer datos de la página de detalle
                    property_url = urljoin(self.base_url, link['href'])
                    property_data = self.extract_property_from_detail_page(property_url)
                    
                    if property_data:
                        properties.append(property_data)
                        logger.info(f"✓ Propiedad extraída: €{property_data['price']:,} - {property_data['title'][:50]}...")
                    
                    # Pausa entre extracciones
                    time.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    logger.error(f"Error procesando enlace {link.get('href', '')}: {e}")
                    continue
            
            logger.info(f"Página procesada: {len(properties)} propiedades válidas extraídas")
            return properties
            
        except requests.RequestException as e:
            logger.error(f"Error de conexión scrapeando {url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado scrapeando {url}: {e}")
            return []

    def run(self):
        """Ejecuta el scraper completo y guarda en base de datos."""
        create_tables()
        
        print(f"🏠 Iniciando scraper de {self.website}...")
        print("=" * 50)
        
        all_properties = []
        page = 1
        max_pages = 10
        
        while page <= max_pages:
            if page == 1:
                url = self.search_url
            else:
                url = f"{self.search_url}{page}/"
            
            properties = self.scrape_page(url)
            
            if not properties:
                logger.info(f"No se encontraron más propiedades en página {page}. Finalizando.")
                break
            
            all_properties.extend(properties)
            logger.info(f"Página {page}: {len(properties)} propiedades | Total acumulado: {len(all_properties)}")
            
            page += 1
            
            # Pausa entre páginas
            time.sleep(random.uniform(2, 4))
        
        # Guardar en base de datos
        if all_properties:
            repo = PropertyRepository()
            saved_count = 0
            
            for prop in all_properties:
                try:
                    # Adaptar los datos al formato esperado por PropertyRepository
                    property_data = {
                        'reference': f"pisos.com-{prop['url'].split('/')[-2]}" if prop['url'] else 'N/A',
                        'operation': 'venta',
                        'price': prop['price'],
                        'rooms': prop['rooms'],
                        'bathrooms': prop['bathrooms'],
                        'surface': prop['square_meters'],
                        'title': prop['title'],
                        'location': prop['location'],
                        'address': prop['location'],
                        'url': prop['url'],
                        'website': prop['source']
                    }
                    
                    success = repo.save_property(property_data)
                    if success:
                        saved_count += 1
                except Exception as e:
                    logger.error(f"Error guardando propiedad: {e}")
                    continue
            
            print(f"\n📊 Resultados del scraping de {self.website}:")
            print(f"Total de propiedades encontradas: {len(all_properties)}")
            print(f"Propiedades guardadas en BD: {saved_count}")
            
        else:
            print(f"❌ No se encontraron propiedades en {self.website}")
        
        logger.info(f"Scraping de {self.website} completado. Total: {len(all_properties)} propiedades")

def main():
    """Función principal para testing."""
    scraper = PisoscomScraper()
    scraper.run()

if __name__ == "__main__":
    main()