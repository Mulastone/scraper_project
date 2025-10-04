#!/bin/bash

# Setup cron job para scrapers automáticos 1 vez al día
# Ejecuta a las 06:00 cada día

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_SCRIPT="$SCRIPT_DIR/run_all_scrapers.sh"

echo "🔧 Configurando cron job para scrapers automáticos diarios..."

# Verificar que el script existe y es ejecutable
if [[ ! -f "$CRON_SCRIPT" ]]; then
    echo "❌ Error: $CRON_SCRIPT no encontrado"
    exit 1
fi

chmod +x "$CRON_SCRIPT"

# Crear entrada de cron - 1 vez al día a las 06:00
CRON_ENTRY="0 6 * * * $CRON_SCRIPT >> /var/log/scrapers_cron.log 2>&1"

# Verificar si ya existe la entrada
if crontab -l 2>/dev/null | grep -q "$CRON_SCRIPT"; then
    echo "ℹ️ Entrada de cron ya existe, actualizando..."
    # Eliminar entrada existente
    crontab -l 2>/dev/null | grep -v "$CRON_SCRIPT" | crontab -
fi

# Añadir nueva entrada
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Cron job configurado exitosamente!"
echo "📅 Se ejecutará diariamente a las 06:00"
echo "📝 Log en: /var/log/scrapers_cron.log"

# Mostrar crontab actual
echo ""
echo "📋 Crontab actual:"
crontab -l

# Crear directorio de logs si no existe
sudo mkdir -p /var/log
sudo touch /var/log/scrapers_cron.log
sudo chmod 666 /var/log/scrapers_cron.log

echo ""
echo "🎯 Para monitorear la ejecución:"
echo "   tail -f /var/log/scrapers_cron.log"
echo ""
echo "🛑 Para detener el cron job:"
echo "   crontab -r"
echo ""
echo "⚡ Para ejecutar manualmente:"
echo "   $CRON_SCRIPT"