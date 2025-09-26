#!/bin/bash

# Script para configurar la base de datos del scraper en PostgreSQL existente
# Uso: ./setup-db.sh

set -e

echo "🗄️ Configurando base de datos del scraper en PostgreSQL existente..."

# Variables (configuración actual del VPS)
DJANGO_CONTAINER="app_db_1"  # Nombre del contenedor PostgreSQL de Django
POSTGRES_USER="ecodisseny_user"  # Usuario de PostgreSQL de Django
POSTGRES_DB="ecodisseny_db"  # Base de datos principal de Django

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# 1. Verificar que el contenedor de PostgreSQL existe
if ! docker ps | grep -q $DJANGO_CONTAINER; then
    echo "❌ Error: Contenedor PostgreSQL '$DJANGO_CONTAINER' no encontrado"
    echo "Containers disponibles:"
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
    exit 1
fi

echo_success "Contenedor PostgreSQL encontrado: $DJANGO_CONTAINER"

# 2. Crear usuario y base de datos para el scraper
echo "🔧 Creando usuario y base de datos para scraper..."

docker exec $DJANGO_CONTAINER psql -U ecodisseny_user -c "
-- Crear usuario para scraper si no existe
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'scraper_user') THEN
        CREATE USER scraper_user WITH PASSWORD '${POSTGRES_PASSWORD}';
    END IF;
END
\$\$;

-- Crear base de datos para scraper si no existe
SELECT 'CREATE DATABASE properties_db OWNER scraper_user' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'properties_db')\gexec

-- Otorgar permisos
GRANT ALL PRIVILEGES ON DATABASE properties_db TO scraper_user;
"

echo_success "Usuario y base de datos creados"

# 3. Crear tabla properties en la nueva base de datos
echo "🏗️ Creando tabla properties..."

docker exec $DJANGO_CONTAINER psql -U scraper_user -d properties_db -c "
CREATE TABLE IF NOT EXISTS properties (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    price DECIMAL(12, 2),
    location TEXT,
    rooms INTEGER,
    bathrooms INTEGER,
    surface DECIMAL(10, 2),
    description TEXT,
    url TEXT UNIQUE,
    website VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para mejor performance
CREATE INDEX IF NOT EXISTS idx_properties_price ON properties(price);
CREATE INDEX IF NOT EXISTS idx_properties_location ON properties(location);
CREATE INDEX IF NOT EXISTS idx_properties_website ON properties(website);
CREATE INDEX IF NOT EXISTS idx_properties_timestamp ON properties(timestamp);

-- Otorgar permisos en la tabla
GRANT ALL PRIVILEGES ON TABLE properties TO scraper_user;
GRANT USAGE, SELECT ON SEQUENCE properties_id_seq TO scraper_user;
"

echo_success "Tabla properties creada con índices"

# 4. Verificar la configuración
echo "🔍 Verificando configuración..."

TABLES=$(docker exec $DJANGO_CONTAINER psql -U scraper_user -d properties_db -t -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
echo_success "Tablas disponibles: $TABLES"

COUNT=$(docker exec $DJANGO_CONTAINER psql -U scraper_user -d properties_db -t -c "SELECT COUNT(*) FROM properties;" | tr -d ' ')
echo_success "Registros en properties: $COUNT"

echo ""
echo "🎉 ¡Base de datos configurada correctamente!"
echo ""
echo "📋 Configuración:"
echo "- Host: $DJANGO_CONTAINER (desde containers) / localhost:5432 (desde host)"
echo "- Base de datos: properties_db" 
echo "- Usuario: scraper_user"
echo "- Tabla principal: properties"
echo ""
echo "🔧 Para usar en el scraper:"
echo "DATABASE_URL=postgresql://scraper_user:${POSTGRES_PASSWORD}@localhost:5432/properties_db"
echo ""
echo "📊 Para probar la conexión:"
echo "docker exec $DJANGO_CONTAINER psql -U scraper_user -d properties_db -c 'SELECT COUNT(*) FROM properties;'"