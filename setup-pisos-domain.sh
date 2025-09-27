#!/bin/bash
# Setup script para pisos.arasmu.net
# Ejecutar después de configurar DNS en Cloudflare

echo "🌐 CONFIGURACIÓN DE pisos.arasmu.net"
echo "===================================="
echo ""

# Verificar DNS
echo "1. 🔍 Verificando DNS..."
if nslookup pisos.arasmu.net 8.8.8.8 > /dev/null 2>&1; then
    echo "✅ DNS configurado correctamente"
    
    # Obtener certificado SSL
    echo ""
    echo "2. 🔐 Obteniendo certificado SSL..."
    sudo certbot --nginx -d pisos.arasmu.net --email mulastone@hotmail.com --agree-tos --no-eff-email
    
    if [ $? -eq 0 ]; then
        echo "✅ Certificado SSL obtenido exitosamente"
        echo ""
        echo "🎉 ¡Configuración completada!"
        echo "✅ Acceso seguro: https://pisos.arasmu.net"
    else
        echo "❌ Error obteniendo certificado SSL"
        echo "ℹ️  Acceso temporal: http://pisos.arasmu.net"
    fi
    
else
    echo "❌ DNS no configurado. Pasos pendientes:"
    echo ""
    echo "📋 PASOS A SEGUIR:"
    echo "1. Ir a Cloudflare → arasmu.net → DNS Records"
    echo "2. Agregar registro A:"
    echo "   - Tipo: A"
    echo "   - Nombre: pisos"
    echo "   - Contenido: 161.97.147.142"
    echo "   - Proxy: ✅ Activado (naranja)"
    echo "3. Esperar 2-10 minutos para propagación"
    echo "4. Ejecutar este script nuevamente"
    echo ""
    echo "⏳ Verificando propagación cada 30 segundos..."
    
    # Loop de verificación
    while ! nslookup pisos.arasmu.net 8.8.8.8 > /dev/null 2>&1; do
        echo "⏳ DNS aún no propagado... esperando..."
        sleep 30
    done
    
    echo "✅ DNS propagado! Ejecutando certificado SSL..."
    sudo certbot --nginx -d pisos.arasmu.net --email mulastone@hotmail.com --agree-tos --no-eff-email
fi

# Verificar estado final
echo ""
echo "📊 ESTADO FINAL:"
echo "================"
echo "🌐 Dominio: pisos.arasmu.net"
echo "🔧 Nginx: $(sudo systemctl is-active nginx)"
echo "🐳 Streamlit: $(docker ps --filter name=scraper_streamlit_prod --format "{{.Status}}")"
echo ""

if curl -s -k https://pisos.arasmu.net > /dev/null 2>&1; then
    echo "✅ HTTPS funcionando: https://pisos.arasmu.net"
elif curl -s http://pisos.arasmu.net > /dev/null 2>&1; then
    echo "⚠️  Solo HTTP disponible: http://pisos.arasmu.net"
else
    echo "❌ Sitio no accesible"
fi

echo ""
echo "🔗 URLs de acceso:"
echo "  - Dominio: https://pisos.arasmu.net (principal)"
echo "  - IP directa: http://161.97.147.142:8518 (backup)"
echo "  - Ruta IP: http://161.97.147.142/scraper/ (backup)"