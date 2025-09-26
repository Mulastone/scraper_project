#!/bin/bash

# Script de despliegue desde GitHub al VPS
# Uso: ./deploy-from-github.sh [branch]

set -e

# Variables (ajustar según tu configuración)
GITHUB_REPO="https://github.com/tu-usuario/scraper-andorra.git"  # ⚠️ CAMBIAR
BRANCH="${1:-main}"
PROJECT_DIR="/opt/scraper-project"
DOMAIN="scraper.arasmu.net"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() { echo -e "${BLUE}ℹ️ $1${NC}"; }
echo_success() { echo -e "${GREEN}✅ $1${NC}"; }
echo_warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }

echo_info "🚀 Desplegando Scraper Dashboard desde GitHub..."
echo_info "Repositorio: $GITHUB_REPO"
echo_info "Rama: $BRANCH"

# 1. Verificar que estamos en el VPS
if [ ! -f /etc/nginx/nginx.conf ]; then
    echo "❌ Error: Este script debe ejecutarse en el VPS"
    exit 1
fi

# 2. Instalar Git si no existe
if ! command -v git &> /dev/null; then
    echo_info "📦 Instalando Git..."
    apt update && apt install -y git
fi

# 3. Clonar o actualizar repositorio
if [ -d "$PROJECT_DIR" ]; then
    echo_info "🔄 Actualizando repositorio existente..."
    cd "$PROJECT_DIR"
    git fetch origin
    git reset --hard origin/$BRANCH
    git clean -fd
else
    echo_info "📥 Clonando repositorio..."
    git clone -b $BRANCH $GITHUB_REPO $PROJECT_DIR
    cd "$PROJECT_DIR"
fi

echo_success "Código actualizado desde GitHub"

# 4. Configurar variables de entorno
if [ ! -f ".env" ]; then
    echo_warning "Configurando variables de entorno por primera vez..."
    cp .env.template .env
    
    # Generar password seguro
    RANDOM_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    sed -i "s/CAMBIAR_POR_PASSWORD_SEGURO/$RANDOM_PASSWORD/" .env
    
    echo_warning "⚠️ Password generado automáticamente. Revisa el archivo .env"
    echo_info "Password PostgreSQL: $RANDOM_PASSWORD"
else
    echo_success "Archivo .env existente mantenido"
fi

# 5. Cargar variables de entorno
source .env

# 6. Verificar containers de Django existentes
echo_info "🔍 Verificando configuración de Docker..."
DJANGO_DB=$(docker ps --filter "name=app_db" --format "{{.Names}}" | head -1)
DJANGO_NETWORK=$(docker network ls --filter "name=app_default" --format "{{.Name}}" | head -1)

if [ -z "$DJANGO_DB" ]; then
    echo "❌ Error: Container PostgreSQL de Django no encontrado"
    echo "Containers disponibles:"
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
    exit 1
fi

echo_success "PostgreSQL Django encontrado: $DJANGO_DB"
echo_success "Network encontrado: $DJANGO_NETWORK"

# 7. Configurar base de datos
echo_info "🗄️ Configurando base de datos..."
docker exec $DJANGO_DB psql -U ecodisseny_user -c "
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'scraper_user') THEN
        CREATE USER scraper_user WITH PASSWORD '$POSTGRES_PASSWORD';
    END IF;
END
\$\$;

SELECT 'CREATE DATABASE properties_db OWNER scraper_user' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'properties_db')\gexec

GRANT ALL PRIVILEGES ON DATABASE properties_db TO scraper_user;
" || echo_warning "Usuario/BD pueden ya existir"

# Crear tabla properties
docker exec $DJANGO_DB psql -U scraper_user -d properties_db -c "
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

CREATE INDEX IF NOT EXISTS idx_properties_price ON properties(price);
CREATE INDEX IF NOT EXISTS idx_properties_location ON properties(location);
CREATE INDEX IF NOT EXISTS idx_properties_website ON properties(website);
CREATE INDEX IF NOT EXISTS idx_properties_timestamp ON properties(timestamp);

GRANT ALL PRIVILEGES ON TABLE properties TO scraper_user;
GRANT USAGE, SELECT ON SEQUENCE properties_id_seq TO scraper_user;
" || echo_warning "Tabla puede ya existir"

echo_success "Base de datos configurada"

# 8. Actualizar configuración Docker con nombres reales
echo_info "🔧 Actualizando configuración Docker..."
sed -i "s/app_db_1/$DJANGO_DB/g" docker-compose.shared-db.yml
sed -i "s/app_default/$DJANGO_NETWORK/g" docker-compose.shared-db.yml

# 9. Parar containers anteriores si existen
echo_info "⏹️ Parando containers anteriores..."
docker-compose -f docker-compose.shared-db.yml down || true

# 10. Construir y lanzar containers
echo_info "🐳 Construyendo y lanzando containers..."
docker-compose -f docker-compose.shared-db.yml build --no-cache
docker-compose -f docker-compose.shared-db.yml up -d streamlit

# 11. Configurar archivos estáticos
echo_info "📁 Configurando archivos estáticos..."
mkdir -p /var/www/scraper/static
cp -r static/* /var/www/scraper/static/ || echo_warning "Archivos estáticos no encontrados"

# 12. Configurar Nginx
echo_info "🌐 Configurando Nginx..."
cp nginx-scraper.conf /etc/nginx/sites-available/$DOMAIN
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 13. SSL (si no existe)
if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    echo_info "🔒 Configurando SSL..."
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@arasmu.net
else
    echo_success "SSL ya configurado"
fi

# 14. Ejecutar scraper inicial
echo_info "🕷️ Ejecutando scraper inicial..."
sleep 10
docker-compose -f docker-compose.shared-db.yml run --rm scraper || echo_warning "Scraper inicial falló, se puede ejecutar después"

# 15. Configurar cron job
echo_info "⏰ Configurando cron job..."
CRON_JOB="0 2 * * * cd $PROJECT_DIR && docker-compose -f docker-compose.shared-db.yml run --rm scraper > /var/log/scraper.log 2>&1"
(crontab -l 2>/dev/null | grep -v "scraper"; echo "$CRON_JOB") | crontab -

# 16. Verificación final
echo_info "🔍 Verificación final..."
sleep 5

if curl -f https://$DOMAIN > /dev/null 2>&1; then
    echo_success "✅ Dashboard funcionando correctamente!"
else
    echo_warning "⚠️ Dashboard puede necesitar unos minutos para estar disponible"
fi

# 17. Información final
echo ""
echo_success "🎉 ¡Despliegue completado desde GitHub!"
echo ""
echo_info "📊 Información del despliegue:"
echo "- 🌍 URL: https://$DOMAIN"
echo "- 🗄️ Base de datos: $DJANGO_DB/properties_db"
echo "- 🐳 Containers: scraper_streamlit_prod"
echo "- ⏰ Cron: Cada día a las 2:00 AM"
echo ""
echo_info "🔧 Comandos útiles:"
echo "- Ver logs: docker-compose -f $PROJECT_DIR/docker-compose.shared-db.yml logs -f streamlit"
echo "- Ejecutar scraper: docker-compose -f $PROJECT_DIR/docker-compose.shared-db.yml run --rm scraper"
echo "- Actualizar: cd $PROJECT_DIR && git pull && docker-compose -f docker-compose.shared-db.yml build && docker-compose -f docker-compose.shared-db.yml up -d"
echo ""
echo_success "🔄 Para futuras actualizaciones, simplemente ejecuta: ./deploy-from-github.sh"