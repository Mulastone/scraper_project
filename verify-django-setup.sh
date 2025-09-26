#!/bin/bash

# Script de verificación específico para la configuración de Django actual
# Uso: ./verify-django-setup.sh

echo "🔍 Verificando configuración específica de Django..."

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo_info() { echo -e "${BLUE}ℹ️ $1${NC}"; }
echo_success() { echo -e "${GREEN}✅ $1${NC}"; }
echo_warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
echo_error() { echo -e "${RED}❌ $1${NC}"; }

# 1. Verificar containers específicos
echo_info "Verificando containers de Django..."

WEB_CONTAINER=$(docker ps --filter "name=app_web" --format "{{.Names}}" | head -1)
DB_CONTAINER=$(docker ps --filter "name=app_db" --format "{{.Names}}" | head -1)

if [ ! -z "$WEB_CONTAINER" ]; then
    echo_success "Container Web encontrado: $WEB_CONTAINER"
else
    echo_error "Container Web de Django no encontrado"
fi

if [ ! -z "$DB_CONTAINER" ]; then
    echo_success "Container DB encontrado: $DB_CONTAINER"
else
    echo_error "Container DB de Django no encontrado"
fi

# 2. Verificar network
echo_info "Verificando network..."
NETWORK=$(docker network ls --filter "name=app_default" --format "{{.Name}}" | head -1)
if [ ! -z "$NETWORK" ]; then
    echo_success "Network encontrado: $NETWORK"
    
    echo_info "Containers en el network:"
    docker network inspect $NETWORK --format='{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{"\n"}}{{end}}'
else
    echo_warning "Network app_default no encontrado automáticamente"
    echo_info "Networks disponibles:"
    docker network ls
fi

# 3. Verificar acceso a PostgreSQL
if [ ! -z "$DB_CONTAINER" ]; then
    echo_info "Verificando acceso a PostgreSQL..."
    
    # Verificar con usuario de Django
    if docker exec $DB_CONTAINER psql -U ecodisseny_user -d ecodisseny_db -c "SELECT version();" > /dev/null 2>&1; then
        echo_success "Conexión exitosa con usuario ecodisseny_user"
        
        echo_info "Información de la base de datos:"
        docker exec $DB_CONTAINER psql -U ecodisseny_user -d ecodisseny_db -c "
        SELECT 
            'Base de datos: ' || current_database() as info
        UNION ALL
        SELECT 'Usuario actual: ' || current_user
        UNION ALL 
        SELECT 'Versión PostgreSQL: ' || version();
        "
    else
        echo_error "No se pudo conectar con usuario ecodisseny_user"
    fi
fi

# 4. Generar configuración exacta
echo ""
echo_info "📋 Configuración detectada para docker-compose.shared-db.yml:"
echo ""
cat << EOF
networks:
  $NETWORK:
    external: true

services:
  streamlit:
    environment:
      - DATABASE_URL=postgresql://scraper_user:\${POSTGRES_PASSWORD}@$DB_CONTAINER:5432/properties_db
    networks:
      - $NETWORK
  
  scraper:
    environment:
      - DATABASE_URL=postgresql://scraper_user:\${POSTGRES_PASSWORD}@$DB_CONTAINER:5432/properties_db  
    networks:
      - $NETWORK
EOF

# 5. Comandos para configurar la base de datos del scraper
echo ""
echo_info "🔧 Comandos para configurar base de datos del scraper:"
echo ""
echo "# 1. Crear usuario scraper_user:"
echo "docker exec $DB_CONTAINER psql -U ecodisseny_user -d ecodisseny_db -c \"CREATE USER scraper_user WITH PASSWORD 'tu_password';\""
echo ""
echo "# 2. Crear base de datos properties_db:"
echo "docker exec $DB_CONTAINER psql -U ecodisseny_user -d ecodisseny_db -c \"CREATE DATABASE properties_db OWNER scraper_user;\""
echo ""
echo "# 3. Verificar conexión:"
echo "docker exec $DB_CONTAINER psql -U scraper_user -d properties_db -c \"SELECT 'Conexión exitosa' as resultado;\""

# 6. Estado general
echo ""
echo_info "📊 Estado general del sistema:"
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | head -10