#!/usr/bin/env python3
"""
Script para limpiar la base de datos de propiedades
"""
import os
import sys
sys.path.append('/app')  # Para Docker

from src.database.operations import PropertyRepository

def clear_database():
    """Limpia toda la base de datos de propiedades"""
    try:
        # Usar SQLAlchemy directamente
        from src.database.connection import engine
        from sqlalchemy import text
        
        # Contar antes
        with engine.connect() as conn:
            result_before = conn.execute(text("SELECT COUNT(*) FROM properties"))
            count_before = result_before.fetchone()[0]
            print(f"📊 Propiedades antes de limpiar: {count_before}")
            
            # Limpiar base de datos
            result_delete = conn.execute(text("DELETE FROM properties"))
            conn.commit()
            
            # Verificar después
            result_after = conn.execute(text("SELECT COUNT(*) FROM properties"))
            count_after = result_after.fetchone()[0]
            
            print(f"🧹 Base de datos limpiada exitosamente")
            print(f"📊 Propiedades eliminadas: {count_before}")
            print(f"📊 Propiedades restantes: {count_after}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error limpiando base de datos: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧹 LIMPIANDO BASE DE DATOS...")
    print("=" * 40)
    
    success = clear_database()
    
    if success:
        print("✅ Base de datos limpiada correctamente")
        sys.exit(0)
    else:
        print("❌ Error limpiando base de datos")
        sys.exit(1)