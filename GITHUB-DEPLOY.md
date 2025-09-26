# 🚀 Despliegue desde GitHub

## 📋 Pasos para el despliegue inicial

### 1. Preparar repositorio en GitHub

```bash
# En tu máquina local
cd /home/mulastone/proyectos/scraper-project

# Inicializar git (si no está inicializado)
git init

# Añadir archivos
git add .
git commit -m "Initial commit: Scraper Dashboard Andorra"

# Conectar con GitHub (crear repositorio primero en github.com)
git remote add origin https://github.com/TU-USUARIO/scraper-andorra.git
git branch -M main
git push -u origin main
```

### 2. Desplegar en VPS

```bash
# Conectar al VPS
ssh root@161.97.147.142

# Descargar y ejecutar script de despliegue
wget https://raw.githubusercontent.com/TU-USUARIO/scraper-andorra/main/deploy-from-github.sh
chmod +x deploy-from-github.sh

# Editar variables si es necesario
nano deploy-from-github.sh  # Cambiar GITHUB_REPO por tu URL

# Ejecutar despliegue
./deploy-from-github.sh
```

### 3. Verificar despliegue

- Dashboard: https://scraper.arasmu.net
- Logs: `docker-compose -f /opt/scraper-project/docker-compose.shared-db.yml logs -f streamlit`

## 🔄 Actualizaciones posteriores

### Desde tu máquina local:

```bash
# Hacer cambios al código
git add .
git commit -m "Descripción de cambios"
git push origin main
```

### En el VPS:

```bash
cd /opt/scraper-project
./update-from-github.sh
```

## 📁 Archivos importantes

- **`.env.template`**: Template de variables de entorno
- **`.gitignore`**: Archivos excluidos del repositorio
- **`deploy-from-github.sh`**: Script de despliegue inicial completo
- **`update-from-github.sh`**: Script de actualización rápida
- **`docker-compose.shared-db.yml`**: Configuración para PostgreSQL compartido

## 🔒 Seguridad

- ❌ **NO subir** archivos `.env` con passwords reales
- ✅ **Usar** `.env.template` como plantilla
- ✅ **Configurar** variables sensibles en el VPS
- ✅ **Revisar** `.gitignore` antes del primer commit

## 🛠️ Variables de entorno importantes

En el VPS, editar `/opt/scraper-project/.env`:

```bash
POSTGRES_PASSWORD=tu_password_seguro_aqui
```

## 📊 Monitoreo

```bash
# Ver estado
docker ps

# Ver logs en tiempo real
docker-compose -f /opt/scraper-project/docker-compose.shared-db.yml logs -f

# Ejecutar scraper manualmente
docker-compose -f /opt/scraper-project/docker-compose.shared-db.yml run --rm scraper

# Verificar base de datos
docker exec -it app_db_1 psql -U scraper_user -d properties_db -c "SELECT COUNT(*) FROM properties;"
```

## 🚨 Troubleshooting

### Error: "Container PostgreSQL de Django no encontrado"

```bash
# Verificar containers existentes
docker ps | grep postgres

# Actualizar nombre en docker-compose.shared-db.yml si es diferente
```

### Error: "Network no encontrado"

```bash
# Listar networks
docker network ls

# Actualizar nombre del network en docker-compose.shared-db.yml
```

### Dashboard no carga

```bash
# Verificar Nginx
nginx -t
systemctl status nginx

# Verificar SSL
certbot certificates

# Verificar container Streamlit
docker logs scraper_streamlit_prod
```
