from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .connection import get_connection, close_connection
from ..models.property import Property

class PropertyRepository:
    
    @staticmethod
    def save_property(property_data: dict) -> bool:
        """
        Guarda una propiedad en la base de datos
        """
        session = get_connection()
        if not session:
            return False
            
        try:
            # Verificar si la URL ya existe
            existing = session.query(Property).filter_by(url=property_data.get('url')).first()
            if existing:
                print(f"Propiedad ya existe: {property_data.get('url')}")
                return True
            
            # Crear nueva propiedad
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