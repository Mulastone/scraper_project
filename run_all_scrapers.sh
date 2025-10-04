#!/bin/bash
# Script para ejecutar TODOS los scrapers automáticamente (para cron job)
# Optimizado con batch processing

echo "🚀 INICIANDO SCRAPING COMPLETO - $(date)"
echo "=================================================="

# Variables de configuración
DOCKER_NETWORK="ecodisseny_dj_pg_default"
DATABASE_URL="postgresql://ecodisseny_user:ecodisseny_password123@ecodisseny_dj_pg_db_1:5432/properties_db"
DOCKER_IMAGE="scraper_project_scraper"
PROJECT_DIR="/root/scraper_project"

start_time=$(date +%s)

echo "📋 Ejecutando todos los scrapers con runner optimizado..."
echo ""

# Ejecutar todos los scrapers usando el runner con timeout de 60 minutos
timeout 3600 docker run --rm \
    --network "$DOCKER_NETWORK" \
    -e DATABASE_URL="$DATABASE_URL" \
    -v "$PROJECT_DIR:/app" \
    -w /app \
    "$DOCKER_IMAGE" \
    python -c "from src.scrapers.runner import run_all_scrapers; run_all_scrapers()"

exit_code=$?
end_time=$(date +%s)
execution_time=$((end_time - start_time))

echo ""
echo "=================================================="

if [ $exit_code -eq 0 ]; then
    echo "✅ SCRAPING COMPLETADO EXITOSAMENTE"
else
    echo "❌ ERROR EN EL SCRAPING (código: $exit_code)"
fi

echo "⏱️  Tiempo total: ${execution_time} segundos"

# Estadísticas de vigencia después del scraping
echo ""
echo "📊 ESTADÍSTICAS DE VIGENCIA:"
echo "----------------------------"

docker run --rm \
    --network "$DOCKER_NETWORK" \
    -e DATABASE_URL="$DATABASE_URL" \
    -v "$PROJECT_DIR:/app" \
    -w /app \
    "$DOCKER_IMAGE" \
    python -c "
from src.database.connection import engine
from sqlalchemy import text
from datetime import datetime, timedelta

with engine.connect() as conn:
    # Total de propiedades
    total_result = conn.execute(text('SELECT COUNT(*) FROM properties WHERE price IS NOT NULL AND price > 0'))
    total = total_result.fetchone()[0]
    
    # Propiedades vigentes (menos de 3 días)
    vigent_result = conn.execute(text(
        'SELECT COUNT(*) FROM properties WHERE price IS NOT NULL AND price > 0 AND scraping_date >= %s'
    ), (datetime.now() - timedelta(days=3),))
    vigent = vigent_result.fetchone()[0]
    
    # Propiedades inactivas (más de 7 días)
    inactive_result = conn.execute(text(
        'SELECT COUNT(*) FROM properties WHERE price IS NOT NULL AND price > 0 AND scraping_date < %s'
    ), (datetime.now() - timedelta(days=7),))
    inactive = inactive_result.fetchone()[0]
    
    vigency_percentage = (vigent / total * 100) if total > 0 else 0
    
    print(f'📈 Total propiedades: {total}')
    print(f'🟢 Propiedades vigentes (≤3 días): {vigent} ({vigency_percentage:.1f}%)')
    print(f'🔴 Propiedades inactivas (≥7 días): {inactive}')
    
    # Ubicaciones especiales
    special_result = conn.execute(text(
        \"SELECT location, COUNT(*) as count FROM properties WHERE location IN ('Pas de la Casa', 'Arinsal', 'Bordes d\\'Envalira') AND price IS NOT NULL AND price > 0 GROUP BY location ORDER BY count DESC\"
    ))
    
    print('')
    print('🏔️  Ubicaciones especiales detectadas:')
    for row in special_result:
        print(f'   • {row[0]}: {row[1]} propiedades')
"

echo ""
echo "🏁 PROCESO COMPLETO FINALIZADO - $(date)"
echo "=================================================="

exit $exit_code