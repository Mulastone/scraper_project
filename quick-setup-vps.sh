#!/bin/bash

# Configuración rápida para VPS con Django existente
# Ejecutar EN EL VPS después de subir los archivos

echo "🚀 Configuración rápida en VPS..."

# 1. Configurar base de datos en PostgreSQL existente
echo "🗄️ Configurando base de datos..."

# Variables detectadas de tu VPS
DB_CONTAINER="app_db_1"
SCRAPER_PASSWORD="Scr4p3r_Andorra_2025!"  # Cambiar por una contraseña segura

# Crear usuario y base de datos para scraper
docker exec $DB_CONTAINER psql -U ecodisseny_user -c "
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'scraper_user') THEN
        CREATE USER scraper_user WITH PASSWORD '$SCRAPER_PASSWORD';
    END IF;
END
\$\$;

SELECT 'CREATE DATABASE properties_db OWNER scraper_user' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'properties_db')\gexec

GRANT ALL PRIVILEGES ON DATABASE properties_db TO scraper_user;
"

# Crear tabla properties
docker exec $DB_CONTAINER psql -U scraper_user -d properties_db -c "
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
"

# 2. Configurar variables de entorno
echo "POSTGRES_PASSWORD=$SCRAPER_PASSWORD" > .env

# 3. Lanzar containers
echo "🐳 Lanzando containers..."
docker-compose -f docker-compose.shared-db.yml build
docker-compose -f docker-compose.shared-db.yml up -d streamlit

# 4. Configurar nginx
echo "🌐 Configurando Nginx..."
cp nginx-scraper.conf /etc/nginx/sites-available/scraper.arasmu.net
ln -sf /etc/nginx/sites-available/scraper.arasmu.net /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 5. SSL
echo "🔒 Para configurar SSL ejecuta:"
echo "certbot --nginx -d scraper.arasmu.net"

# 6. Ejecutar scraper inicial
echo "🕷️ Ejecutando scraper inicial..."
sleep 10
docker-compose -f docker-compose.shared-db.yml run --rm scraper

# 7. Cron job
echo "⏰ Configurando cron..."
echo "0 2 * * * cd /opt/scraper-project && docker-compose -f docker-compose.shared-db.yml run --rm scraper > /var/log/scraper.log 2>&1" | crontab -

echo "✅ ¡Configuración completada!"
echo "🌍 Dashboard: https://scraper.arasmu.net"
echo "📊 Logs: docker-compose -f docker-compose.shared-db.yml logs -f streamlit"