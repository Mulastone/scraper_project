#!/bin/bash

# Script de prueba para verificar la nueva funcionalidad de vigencia
echo "🧪 PROBANDO NUEVA FUNCIONALIDAD DE VIGENCIA"
echo "==========================================="

echo ""
echo "1️⃣ Ejecutando un scraper para probar actualización de fechas..."

# Ejecutar solo un scraper pequeño para probar
cd /root/scraper_project
docker exec pisos_streamlit_prod python -c "
import sys
sys.path.append('/app')
from src.scrapers.claus_sql import ClausScraper

print('🔬 Ejecutando ClausScraper para prueba...')
scraper = ClausScraper()
result = scraper.scrape()
print(f'✅ Resultado: {result}')
"

echo ""
echo "2️⃣ Verificando estadísticas de vigencia..."

# Mostrar estadísticas
docker exec pisos_streamlit_prod python -c "
import sys
sys.path.append('/app')
import os
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://ecodisseny_user:ecodisseny_password123@ecodisseny_dj_pg_db_1:5432/properties_db')
engine = create_engine(DATABASE_URL)

try:
    print('📊 ESTADÍSTICAS DE VIGENCIA:')
    print('----------------------------')
    
    # Total propiedades
    query_total = 'SELECT COUNT(*) as total FROM properties WHERE price IS NOT NULL AND price > 0'
    result_total = pd.read_sql(query_total, engine)
    total = result_total.iloc[0]['total']
    print(f'📈 Total propiedades: {total:,}')
    
    # Vistas hoy
    today = datetime.now().date()
    query_today = f\"SELECT COUNT(*) as today FROM properties WHERE DATE(scraping_date) = '{today}' AND price IS NOT NULL AND price > 0\"
    result_today = pd.read_sql(query_today, engine)
    today_count = result_today.iloc[0]['today']
    print(f'🆕 Vistas hoy: {today_count:,}')
    
    # Vigentes (últimos 3 días)
    three_days_ago = datetime.now() - timedelta(days=3)
    query_vigentes = f\"SELECT COUNT(*) as vigentes FROM properties WHERE scraping_date >= '{three_days_ago}' AND price IS NOT NULL AND price > 0\"
    result_vigentes = pd.read_sql(query_vigentes, engine)
    vigentes = result_vigentes.iloc[0]['vigentes']
    print(f'✅ Vigentes (3 días): {vigentes:,}')
    
    # No vistas en 7+ días
    week_ago = datetime.now() - timedelta(days=7)
    query_old = f\"SELECT COUNT(*) as old FROM properties WHERE scraping_date < '{week_ago}' AND price IS NOT NULL AND price > 0\"
    result_old = pd.read_sql(query_old, engine)
    old = result_old.iloc[0]['old']
    print(f'⚠️ No vistas 7+ días: {old:,}')
    
    # Porcentaje de vigencia
    vigencia_pct = (vigentes / total * 100) if total > 0 else 0
    print(f'📊 Porcentaje vigencia: {vigencia_pct:.1f}%')
    
    print('')
    print('🕐 DISTRIBUCIÓN POR FECHA DE ÚLTIMA VEZ VISTA:')
    print('----------------------------------------------')
    
    # Últimas actualizaciones por día
    query_dates = \"\"\"
    SELECT DATE(scraping_date) as date, COUNT(*) as count 
    FROM properties 
    WHERE price IS NOT NULL AND price > 0 
    GROUP BY DATE(scraping_date) 
    ORDER BY date DESC 
    LIMIT 7
    \"\"\"
    result_dates = pd.read_sql(query_dates, engine)
    
    for _, row in result_dates.iterrows():
        print(f'   {row[\"date\"]}: {row[\"count\"]:,} propiedades')
    
except Exception as e:
    print(f'❌ Error: {e}')
"

echo ""
echo "3️⃣ Verificando configuración de cron..."
echo "Configuración actual de cron:"
crontab -l | grep scrapers || echo "   No hay cron configurado aún"

echo ""
echo "🎯 PARA ACTIVAR CRON DIARIO:"
echo "   ./setup_cron.sh"
echo ""
echo "📋 PARA MONITOREAR:"
echo "   tail -f /var/log/scrapers_cron.log"