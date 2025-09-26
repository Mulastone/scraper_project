#!/bin/bash

# Script simple para actualizar el proyecto desde GitHub
# Uso: ./update-from-github.sh

set -e

PROJECT_DIR="/opt/scraper-project"

echo "🔄 Actualizando Scraper Dashboard desde GitHub..."

cd $PROJECT_DIR

# 1. Actualizar código
echo "📥 Descargando últimos cambios..."
git fetch origin
git reset --hard origin/main
git clean -fd

# 2. Reconstruir y reiniciar
echo "🐳 Reconstruyendo containers..."
docker-compose -f docker-compose.shared-db.yml build --no-cache
docker-compose -f docker-compose.shared-db.yml up -d

# 3. Actualizar archivos estáticos
echo "📁 Actualizando archivos estáticos..."
cp -r static/* /var/www/scraper/static/ 2>/dev/null || true

# 4. Recargar Nginx
echo "🌐 Recargando Nginx..."
nginx -t && systemctl reload nginx

echo "✅ ¡Actualización completada!"
echo "🌍 Verifica en: https://scraper.arasmu.net"