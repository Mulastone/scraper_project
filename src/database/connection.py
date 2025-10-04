from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://scraper_user:scraper_password@localhost:5432/properties_db"
)

# Crear el motor de base de datos
engine = create_engine(DATABASE_URL, echo=False)

# Crear la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

def get_connection() -> Session:
    """
    Obtiene una conexión a la base de datos PostgreSQL
    Retorna una sesión de SQLAlchemy
    """
    try:
        session = SessionLocal()
        # Comentado para evitar spam en batch processing
        # print("Conexión exitosa a la base de datos PostgreSQL.")
        return session
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def create_tables():
    """
    Crea todas las tablas definidas en los modelos
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("Tablas creadas exitosamente.")
    except Exception as e:
        print(f"Error al crear las tablas: {e}")

def close_connection(session: Session):
    """
    Cierra la conexión de forma segura
    """
    if session:
        session.close()