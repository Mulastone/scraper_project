#!/bin/bash

# Script para configurar SSL para pisos.arasmu.net
# Ejecutar cuando el DNS se haya propagado

echo "🔒 Configurando SSL para pisos.arasmu.net"

# 1. Verificar que el DNS esté propagado
echo "1. Verificando DNS..."
if ! nslookup pisos.arasmu.net 8.8.8.8 > /dev/null 2>&1; then
    echo "❌ DNS aún no propagado. Espera unos minutos y vuelve a intentar."
    echo "   Puedes verificar manualmente: nslookup pisos.arasmu.net 8.8.8.8"
    exit 1
fi

echo "✅ DNS propagado correctamente"

# 2. Verificar que nginx esté funcionando
echo "2. Verificando nginx..."
if ! sudo nginx -t; then
    echo "❌ Configuración de nginx incorrecta"
    exit 1
fi

echo "✅ Nginx configurado correctamente"

# 3. Obtener certificado SSL con Certbot
echo "3. Obteniendo certificado SSL..."
sudo certbot --nginx -d pisos.arasmu.net --non-interactive --agree-tos --email mulastone@hotmail.com

if [ $? -eq 0 ]; then
    echo "✅ Certificado SSL obtenido exitosamente"
    
    # 4. Verificar configuración SSL
    echo "4. Verificando configuración SSL..."
    sudo nginx -t
    sudo systemctl reload nginx
    
    echo "🎉 Configuración completa!"
    echo "   HTTP:  http://pisos.arasmu.net"
    echo "   HTTPS: https://pisos.arasmu.net"
    
else
    echo "❌ Error obteniendo certificado SSL"
    echo "   Verifica que:"
    echo "   - El DNS esté propagado (pisos.arasmu.net → 161.97.147.142)"
    echo "   - El puerto 80 esté abierto"
    echo "   - Nginx esté funcionando"
    exit 1
fi

# 5. Configurar renovación automática
echo "5. Configurando renovación automática..."
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

echo "✅ Renovación automática configurada"
echo ""
echo "🚀 ¡pisos.arasmu.net está listo con SSL!"
echo "   Acceso: https://pisos.arasmu.net"