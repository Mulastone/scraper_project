from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .connection import get_connection, close_connection
from ..models.property import Property

class PropertyRepository:
    
    @staticmethod
    def save_property(property_data: dict) -> bool:
        """
        Guarda una propiedad en la base de datos con historial de precios
        """
        session = get_connection()
        if not session:
            return False
            
        try:
            # Verificar si existe una entrada reciente (mismo día) para evitar duplicados excesivos
            from datetime import datetime, timedelta
            today = datetime.now().date()
            
            existing_today = session.query(Property).filter(
                Property.url == property_data.get('url'),
                Property.scraping_date >= today,
                Property.scraping_date < today + timedelta(days=1)
            ).first()
            
            if existing_today:
                print(f"Propiedad ya existe hoy: {property_data.get('url')}")
                return True
            
            # Crear nueva propiedad (siempre guarda para historial)
            property_obj = Property(
                reference=property_data.get('reference', 'N/A'),
                operation=property_data.get('operation', 'N/A'),
                price=property_data.get('price', 0),
                rooms=property_data.get('rooms', 0),
                bathrooms=property_data.get('bathrooms', 0),
                surface=property_data.get('surface', 0),
                title=property_data.get('title', 'N/A'),
                location=property_data.get('location', 'N/A'),
                address=property_data.get('address', 'N/A'),
                url=property_data.get('url', ''),
                website=property_data.get('website', '')
            )
            
            session.add(property_obj)
            session.commit()
            print(f"Propiedad guardada: {property_data.get('reference')}")
            return True
            
        except IntegrityError as e:
            session.rollback()
            print(f"Error de integridad: {e}")
            return False
        except Exception as e:
            session.rollback()
            print(f"Error al guardar propiedad: {e}")
            return False
        finally:
            close_connection(session)

    @staticmethod
    def save_properties_batch(properties_data: list) -> int:
        """
        Guarda múltiples propiedades en una sola conexión (OPTIMIZADO)
        - Si la propiedad existe: actualiza scraping_date (marca como vigente)
        - Si es nueva: inserta con fecha actual
        Retorna el número de propiedades procesadas exitosamente
        """
        if not properties_data:
            return 0
            
        session = get_connection()
        if not session:
            return 0
            
        processed_count = 0
        new_count = 0
        updated_count = 0
        
        try:
            from datetime import datetime
            current_datetime = datetime.now()
            
            # Obtener todas las URLs existentes en una sola consulta
            existing_properties = {}
            existing_urls = [prop.get('url', '') for prop in properties_data if prop.get('url')]
            
            if existing_urls:
                existing_query = session.query(Property).filter(Property.url.in_(existing_urls)).all()
                existing_properties = {prop.url: prop for prop in existing_query}
            
            # Procesar propiedades en lote
            new_properties = []
            for property_data in properties_data:
                url = property_data.get('url', '')
                
                if url in existing_properties:
                    # Propiedad existe - actualizar fecha de scraping (marca como vigente)
                    existing_prop = existing_properties[url]
                    existing_prop.scraping_date = current_datetime
                    updated_count += 1
                    print(f"🔄 Actualizada fecha vigencia: {url}")
                else:
                    # Propiedad nueva - crear e insertar
                    property_obj = Property(
                        reference=property_data.get('reference', 'N/A'),
                        operation=property_data.get('operation', 'N/A'),
                        price=property_data.get('price', 0),
                        rooms=property_data.get('rooms', 0),
                        bathrooms=property_data.get('bathrooms', 0),
                        surface=property_data.get('surface', 0),
                        title=property_data.get('title', 'N/A'),
                        location=property_data.get('location', 'N/A'),
                        address=property_data.get('address', 'N/A'),
                        url=url,
                        website=property_data.get('website', ''),
                        scraping_date=current_datetime
                    )
                    new_properties.append(property_obj)
                    new_count += 1
            
            # Guardar todas las propiedades nuevas y actualizar las existentes
            if new_properties:
                session.add_all(new_properties)
            
            session.commit()
            processed_count = new_count + updated_count
            
            if new_count > 0:
                print(f"✅ Guardadas {new_count} propiedades NUEVAS")
            if updated_count > 0:
                print(f"🔄 Actualizadas {updated_count} propiedades EXISTENTES (vigentes)")
            if processed_count > 0:
                print(f"📊 Total procesadas: {processed_count}")
            else:
                print("ℹ️ No hay propiedades para procesar")
                
        except Exception as e:
            session.rollback()
            print(f"❌ Error al procesar lote de propiedades: {e}")
            processed_count = 0
        finally:
            close_connection(session)
            
        return processed_count
    
    @staticmethod
    def get_all_properties():
        """
        Obtiene todas las propiedades
        """
        session = get_connection()
        if not session:
            return []
            
        try:
            properties = session.query(Property).all()
            return properties
        except Exception as e:
            print(f"Error al obtener propiedades: {e}")
            return []
        finally:
            close_connection(session)
    
    @staticmethod
    def get_properties_not_seen_since(days: int = 7):
        """
        Obtiene propiedades que no se han visto en los últimos X días
        (probablemente ya no están vigentes)
        """
        session = get_connection()
        if not session:
            return []
            
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            properties = session.query(Property).filter(
                Property.scraping_date < cutoff_date
            ).order_by(Property.scraping_date.desc()).all()
            
            return properties
        except Exception as e:
            print(f"Error al obtener propiedades no vigentes: {e}")
            return []
        finally:
            close_connection(session)
    
    @staticmethod
    def get_vigency_stats():
        """
        Obtiene estadísticas de vigencia de propiedades
        """
        session = get_connection()
        if not session:
            return {}
            
        try:
            from datetime import datetime, timedelta
            
            today = datetime.now()
            yesterday = today - timedelta(days=1)
            week_ago = today - timedelta(days=7)
            
            stats = {}
            
            # Propiedades vistas hoy
            stats['seen_today'] = session.query(Property).filter(
                Property.scraping_date >= today.date()
            ).count()
            
            # Propiedades vistas ayer
            stats['seen_yesterday'] = session.query(Property).filter(
                Property.scraping_date >= yesterday.date(),
                Property.scraping_date < today.date()
            ).count()
            
            # Propiedades no vistas en 7 días
            stats['not_seen_7_days'] = session.query(Property).filter(
                Property.scraping_date < week_ago
            ).count()
            
            # Total propiedades
            stats['total'] = session.query(Property).count()
            
            return stats
            
        except Exception as e:
            print(f"Error al obtener estadísticas de vigencia: {e}")
            return {}
        finally:
            close_connection(session)

    @staticmethod
    def get_property_by_url(url: str):
        """
        Obtiene una propiedad por su URL
        """
        session = get_connection()
        if not session:
            return None
            
        try:
            property_obj = session.query(Property).filter_by(url=url).first()
            return property_obj
        except Exception as e:
            print(f"Error al obtener propiedad: {e}")
            return None
        finally:
            close_connection(session)
    
    @staticmethod
    def get_latest_properties():
        """
        Obtiene las propiedades del último scraping (más recientes)
        """
        session = get_connection()
        if not session:
            return []
            
        try:
            # Subquery para obtener la fecha más reciente por URL
            from sqlalchemy import func
            latest_dates = session.query(
                Property.url,
                func.max(Property.scraping_date).label('max_date')
            ).group_by(Property.url).subquery()
            
            # Propiedades con la fecha más reciente
            properties = session.query(Property).join(
                latest_dates,
                (Property.url == latest_dates.c.url) & 
                (Property.scraping_date == latest_dates.c.max_date)
            ).all()
            
            return properties
        except Exception as e:
            print(f"Error al obtener propiedades más recientes: {e}")
            return []
        finally:
            close_connection(session)
    
    @staticmethod
    def get_price_comparison_by_location():
        """
        Obtiene comparativa de precios medios por ubicación entre scrapings
        """
        session = get_connection()
        if not session:
            return []
            
        try:
            from sqlalchemy import func, distinct
            from datetime import datetime, timedelta
            
            # Obtener fechas de scraping disponibles (últimos 30 días)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            # Precios medios por ubicación y fecha
            price_comparison = session.query(
                Property.location,
                func.date(Property.scraping_date).label('date'),
                func.avg(Property.price).label('avg_price'),
                func.count(Property.id).label('property_count')
            ).filter(
                Property.scraping_date >= thirty_days_ago,
                Property.price > 0
            ).group_by(
                Property.location,
                func.date(Property.scraping_date)
            ).order_by(
                Property.location,
                func.date(Property.scraping_date).desc()
            ).all()
            
            return price_comparison
        except Exception as e:
            print(f"Error al obtener comparativa de precios: {e}")
            return []
        finally:
            close_connection(session)