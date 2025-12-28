from .connection import get_connection, close_connection
from ..models.property import Property

def delete_all_properties():
    """
    Borra todos los registros de la tabla properties.
    """
    session = get_connection()
    if not session:
        print("No se pudo conectar a la base de datos.")
        return
    try:
        deleted = session.query(Property).delete()
        session.commit()
        print(f"{deleted} registros eliminados de properties.")
    except Exception as e:
        session.rollback()
        print(f"Error al eliminar registros: {e}")
    finally:
        close_connection(session)
