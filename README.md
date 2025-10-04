# 🏠 Dashboard Propiedades Andorra - Sistema Automatizado

Dashboard interactivo para visualización de propiedades inmobiliarias en Andorra con scrapers automatizados, sistema de vigencia, filtrado optimizado y interfaz web moderna.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

**🌍 Demo Live**: [pisos.arasmu.net](https://pisos.arasmu.net)

## 🎯 Estado Actual (Octubre 2025)

✅ **Sistema Completamente Automatizado**  
✅ **339 Propiedades Activas** (solo Andorra)  
✅ **4 Scrapers Optimizados** con filtrado inteligente  
✅ **Sistema de Vigencia** (3 días)  
✅ **Filtros por Ubicaciones Especiales** (Pas de la Casa, Arinsal, Bordes d'Envalira)  
✅ **Batch Processing Optimizado**  
✅ **SSL & Dominio pisos.arasmu.net**  
✅ **Cron Diario Automático** (06:00)

## 🏗️ Arquitectura del Sistema

```
scraper-project/
├── 🗄️ Base de Datos (PostgreSQL)
│   └── properties_db (339 propiedades filtradas)
├── 🕷️ Scrapers Python Optimizados
│   ├── pisosad_sql.py        # Scraper pisos.ad (€10k-€450k)
│   ├── nouaire_sql.py        # Scraper principal (1,500+ URLs)
│   ├── expofinques_sql.py    # Scraper expofinques
│   └── claus_sql.py         # Scraper 7claus
├── 📊 Dashboard (Streamlit)
│   └── streamlit_app.py     # Interfaz web con logo ARASMU
├── 🐳 Docker Containers
│   ├── pisos_streamlit_prod # Dashboard web (puerto 8501)
│   └── ecodisseny_dj_pg_db_1 # PostgreSQL
├── 🤖 Automatización
│   ├── run_all_scrapers.sh  # Script principal
│   ├── setup_cron.sh        # Cron diario 06:00
│   └── test_vigencia.sh     # Tests sistema vigencia
└── 🌐 Nginx Proxy
    └── SSL con Let's Encrypt
```

## 🎯 Scrapers Optimizados

| Sitio Web | Scraper | Estado | Filtros Aplicados |
|-----------|---------|--------|-------------------|
| **pisos.ad** | `pisosad_sql.py` | ✅ **100% Funcional** | Precio €10k-€450k + Andorra |
| **nouaire.com** | `nouaire_sql.py` | ✅ Funcionando | Detecta ubicaciones especiales |
| **expofinques.com** | `expofinques_sql.py` | ✅ Funcionando | Filtro Andorra + precio |
| **7claus.com** | `claus_sql.py` | ✅ Funcionando | Validación ubicación |

### 🎯 Filtrado Inteligente Implementado

**Sistema de 3 Etapas:**
1. **Filtro Precio**: Solo propiedades ≤ €450,000
2. **Filtro Andorra**: Validación país con `is_andorra_location()`
3. **Detección Especial**: Pas de la Casa, Arinsal, Bordes d'Envalira

**Palabras clave Andorra:**
```python
andorra_keywords = [
    'andorra', 'escaldes', 'engordany', 'encamp', 'ordino', 
    'canillo', 'massana', 'sant julia', 'loria', 'la vella'
]
```

## 🚀 Instalación y Configuración

### Prerequisitos
- Docker & Docker Compose
- PostgreSQL (contenedor compartido)
- Nginx con SSL
- Python 3.12+

### 🐳 Configuración Docker

```bash
# 1. Construir imagen Streamlit
docker build -f docker/Dockerfile.streamlit -t scraper_project-streamlit .

# 2. Ejecutar contenedor con network host
docker run -d --name pisos_streamlit_prod \
  --network host \
  -e DATABASE_URL="postgresql://scraper_user:scraper_password@localhost:5432/properties_db" \
  scraper_project-streamlit
```

### 🗄️ Base de Datos

```sql
-- Esquema optimizado con sistema de vigencia
CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    price INTEGER NOT NULL,
    rooms INTEGER,
    bathrooms INTEGER,
    surface REAL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    vigencia_date DATE DEFAULT CURRENT_DATE,  -- NUEVO: Sistema vigencia
    website VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    reference VARCHAR(100),
    operation VARCHAR(50) DEFAULT 'venta',
    location VARCHAR(255),
    address TEXT,
    url TEXT UNIQUE NOT NULL
);

-- Índices para rendimiento
CREATE INDEX idx_properties_vigencia ON properties(vigencia_date);
CREATE INDEX idx_properties_price ON properties(price);
CREATE INDEX idx_properties_location ON properties(location);
```

### 🤖 Automatización con Cron

```bash
# Configurar cron diario
chmod +x setup_cron.sh
./setup_cron.sh

# Cron programado: 0 6 * * * (06:00 diario)
crontab -l
```

## 📊 Dashboard Streamlit

### Características Principales

- **🎨 Logo ARASMU** en parte superior del sidebar
- **🏘️ Filtro Poblaciones Invertido**: Por defecto excluye Pas de la Casa, Arinsal, Bordes d'Envalira
- **💰 Rango de Precios**: €10,000 - €450,000
- **🏠 Tipos de Propiedad**: Residenciales por defecto
- **📱 Responsive Design**

### Filtros Implementados

```python
# Tipos residenciales por defecto
tipos_residenciales = ['Piso', 'Apartamento', 'Estudio', 'Duplex', 'Planta baja', 'Ático']

# Poblaciones excluidas por defecto
poblaciones_especiales = ['Pas de la Casa', 'Arinsal', 'Bordes d\'Envalira']
poblaciones_por_defecto = [pob for pob in poblaciones_disponibles 
                          if pob not in poblaciones_especiales]
```

## 🌐 Configuración Nginx

```nginx
# /etc/nginx/sites-enabled/pisos.arasmu.net
server {
    server_name pisos.arasmu.net;
    
    location / {
        proxy_pass http://127.0.0.1:8501/;  # Puerto actualizado
        
        # Headers para Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;
        
        proxy_buffering off;
        proxy_cache_bypass $http_upgrade;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/pisos.arasmu.net/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/pisos.arasmu.net/privkey.pem;
}
```

## 🔧 Scripts de Gestión

### Scripts Principales

```bash
# Ejecutar todos los scrapers
./run_all_scrapers.sh

# Configurar cron automático
./setup_cron.sh

# Test sistema de vigencia
./test_vigencia.sh

# Limpiar base de datos
python clear_database.py
```

### Comandos Docker Útiles

```bash
# Estado de contenedores
docker ps | grep pisos

# Logs en tiempo real
docker logs -f pisos_streamlit_prod

# Recrear contenedor Streamlit
docker stop pisos_streamlit_prod && docker rm pisos_streamlit_prod
docker run -d --name pisos_streamlit_prod --network host \
  -e DATABASE_URL="postgresql://scraper_user:scraper_password@localhost:5432/properties_db" \
  scraper_project-streamlit

# Reiniciar nginx
sudo systemctl reload nginx
```

## 🔍 Sistema de Vigencia

**Funcionamiento:**
- Cada propiedad tiene `vigencia_date = CURRENT_DATE`
- Scrapers actualizan vigencia si URL ya existe
- Propiedades > 3 días se marcan como obsoletas
- Batch processing optimizado para performance

```python
# Actualización de vigencia
cursor.execute("""
    UPDATE properties 
    SET vigencia_date = CURRENT_DATE 
    WHERE url = %s
""", (url,))
```

## 🛠️ Solución de Problemas

### Problemas Comunes

1. **Error credenciales PostgreSQL**
   ```bash
   # Resetear contraseña usuario scraper_user
   docker exec ecodisseny_dj_pg_db_1 psql -U ecodisseny_user -d ecodisseny_db \
     -c "ALTER USER scraper_user PASSWORD 'scraper_password';"
   ```

2. **Nginx 502 Bad Gateway**
   ```bash
   # Verificar puerto correcto en nginx config
   sudo sed -i 's|8518|8501|g' /etc/nginx/sites-enabled/pisos.arasmu.net
   sudo systemctl reload nginx
   ```

3. **Scrapers fallan con variable scope error**
   ```bash
   # Verificar que variables estén declaradas antes de uso
   # En pisosad_sql.py: extraer ubicación ANTES de filtros
   ```

### Debug Commands

```bash
# Test conexión BD desde contenedor
docker exec pisos_streamlit_prod python -c "
from sqlalchemy import create_engine, text
engine = create_engine('postgresql://scraper_user:scraper_password@localhost:5432/properties_db')
with engine.connect() as conn:
    result = conn.execute(text('SELECT count(*) FROM properties'))
    print(f'Propiedades: {result.fetchone()[0]}')
"

# Verificar scrapers
python -c "from src.scrapers.runner import run_all_scrapers; run_all_scrapers()"
```

## 📈 Estadísticas del Sistema

**Base de Datos Optimizada:**
- **Antes**: 696 propiedades (muchas fuera de Andorra)
- **Después**: 339 propiedades (100% Andorra)
- **Filtradas**: 371 propiedades no válidas eliminadas

**Performance:**
- **Tiempo scraping**: ~7-8 minutos para todos los scrapers
- **Batch processing**: Inserción optimizada por lotes
- **Sistema vigencia**: Actualizaciones eficientes

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nuevo-filtro`)
3. Commit cambios (`git commit -m 'Add: filtro por superficie'`)
4. Push (`git push origin feature/nuevo-filtro`)
5. Crear Pull Request

## 📄 Licencia

MIT License - Ver `LICENSE` para detalles.

---

**Desarrollado con ❤️ por Arasmu** | **Dashboard Live**: [pisos.arasmu.net](https://pisos.arasmu.net)

**🔄 Última actualización**: Octubre 2025 - Sistema completamente automatizado y optimizado
| 7claus.com | `claus_sql.py` | 12 | €200k - €600k | ✅ Funcionando |

### 🎯 pisos.ad - Scraper Premium

- **Estrategia Multi-Range**: 3 rangos de precio (10K-400K, 400K-1M, 1M+)
- **Extracción Avanzada**: BeautifulSoup + regex patterns
- **Precios Reales**: €127,000 - €9,500,000 (100% precisión)
- **Deduplicación**: Por URL única
- **Datos Completos**: Precio, habitaciones, baños, superficie, ubicación

**Total Sistema: 1,683 propiedades**

## 🚀 Dashboard Interactivo

### 📊 Funcionalidades Principales

- **🏠 Filtros Inteligentes**: Por tipo (Piso, Apartamento, Estudio, etc.)
- **💰 Rangos de Precio**: 10K€ - 450K€ (personalizable)
- **📍 Ubicaciones**: Todas las parroquias de Andorra
- **📈 Visualizaciones**: Gráficos de barras, mapas de calor
- **🔍 Búsqueda Avanzada**: Por superficie, habitaciones, baños
- **📋 Lista Detallada**: Con enlaces directos a propiedades

### 🎨 Interfaz de Usuario

- **Diseño Responsivo**: Optimizado para desktop y móvil
- **Sidebar Compacto**: Filtros organizados con logo Arasmu
- **Sin Elementos Debug**: Interfaz limpia y profesional
- **Carga Automática**: Datos frescos sin botones innecesarios

## 🐳 Despliegue Docker

### Contenedores en Producción

```bash
# Dashboard Streamlit
pisos_streamlit_prod:
  - Puerto: 127.0.0.1:8518:8501
  - Red: ecodisseny_dj_pg_default
  - BD: ecodisseny_user:ecodisseny_password123

# Scrapers (manual)
pisos_scraper_prod:
  - Ejecución bajo demanda
  - Misma red y BD

# PostgreSQL (externo)
ecodisseny_dj_pg_db_1:
  - Puerto: 5432
  - BD: properties_db
  - Usuario: ecodisseny_user
```

### 🌐 Configuración Nginx

```nginx
# Acceso principal
location /pisos {
    proxy_pass http://localhost:8518/pisos;
    # WebSocket support para Streamlit
}

# Recursos estáticos
location ~ ^/pisos/static/.*$ {
    proxy_pass http://localhost:8518;
    expires 1y;
}

# Redirección automática
location = / {
    return 301 /pisos/;
}
```

## 🗄️ Esquema de Base de Datos

```sql
CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    price INTEGER NOT NULL,
    rooms INTEGER,
    bathrooms INTEGER,
    surface INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    website VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    reference VARCHAR(100),
    operation VARCHAR(50),
    location VARCHAR(255),
    address TEXT,
    url TEXT UNIQUE NOT NULL
);

-- Índices para rendimiento
CREATE INDEX idx_properties_price ON properties(price);
CREATE INDEX idx_properties_website ON properties(website);
CREATE INDEX idx_properties_location ON properties(location);
```

## 🚀 Scripts de Despliegue

### Despliegue Local
```bash
# Setup completo
./deploy-local.sh

# Solo dashboard
docker-compose -f docker-compose.shared-db.yml up -d
```

### Despliegue desde GitHub
```bash
# Deploy automático
./deploy-from-github.sh

# Actualización
./update-from-github.sh
```

### SSL y Dominio
```bash
# Setup DNS (manual en Cloudflare)
# pisos.arasmu.net → 161.97.147.142

# SSL Certificate (después de DNS propagation)
./setup-pisos-ssl.sh
```

## 🔧 Desarrollo y Mantenimiento

### Ejecutar Scrapers Manualmente

```bash
# Todos los scrapers
docker exec pisos_scraper_prod python -m src.scrapers.runner

# Scraper específico
docker exec pisos_scraper_prod python -m src.scrapers.pisosad_sql
```

### Consultas Útiles PostgreSQL

```sql
-- Estado actual
SELECT website, COUNT(*) as propiedades, 
       MIN(price) as precio_min, MAX(price) as precio_max
FROM properties 
WHERE price > 0
GROUP BY website 
ORDER BY propiedades DESC;

-- Propiedades pisos.ad
SELECT title, price, rooms, surface, location, url
FROM properties 
WHERE website = 'pisos.ad'
ORDER BY price DESC;

-- Estadísticas por parroquia
SELECT location, COUNT(*) as total, 
       AVG(price)::INTEGER as precio_promedio
FROM properties 
WHERE location LIKE '%Andorra%'
GROUP BY location 
ORDER BY total DESC;
```

### Debugging y Logs

```bash
# Logs del dashboard
docker logs pisos_streamlit_prod

# Logs de scrapers
docker logs pisos_scraper_prod

# Acceso a PostgreSQL
docker exec -it ecodisseny_dj_pg_db_1 psql -U ecodisseny_user -d properties_db
```

## 📊 Monitorización

### Métricas Actuales (Sep 2025)

- **📈 Total Propiedades**: 1,683
- **💰 Rango Precios**: €85,000 - €9,500,000  
- **🏠 Tipos**: 15+ categorías (Piso, Apartamento, etc.)
- **📍 Ubicaciones**: 7 parroquias + subcategorías
- **⚡ Tiempo Carga**: <3 segundos
- **🔄 Actualización**: Manual bajo demanda

### Health Checks

```bash
# Verificar dashboard
curl -I http://161.97.147.142/pisos/

# Verificar base de datos
docker exec ecodisseny_dj_pg_db_1 pg_isready -U ecodisseny_user

# Verificar contenedores
docker ps | grep pisos
```

## 🛠️ Solución de Problemas

### Problemas Comunes

1. **Dashboard en blanco**: Verificar conexión BD y credenciales
2. **Filtros no funcionan**: Limpiar caché Streamlit
3. **Scrapers fallan**: Verificar estructura HTML de sitios
4. **Nginx 502**: Verificar que contenedor Streamlit esté ejecutándose

### Recovery Commands

```bash
# Reiniciar dashboard
docker restart pisos_streamlit_prod

# Reconstruir desde cero
docker-compose -f docker-compose.shared-db.yml down
docker-compose -f docker-compose.shared-db.yml up -d --build

# Limpiar sistema Docker
docker system prune -f
```

## 🔐 Configuración SSL

### Certificados Let's Encrypt

```bash
# Después de DNS propagation
sudo certbot --nginx -d pisos.arasmu.net

# Auto-renovación
sudo crontab -e
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📈 Roadmap Futuro

- [ ] **Scrapers Adicionales**: Más portales inmobiliarios
- [ ] **API REST**: Endpoint público para datos
- [ ] **Alertas Email**: Notificaciones de nuevas propiedades
- [ ] **Machine Learning**: Predicción de precios
- [ ] **Mobile App**: Aplicación nativa
- [ ] **Multi-idioma**: Catalán, francés, inglés

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nuevo-scraper`)
3. Commit cambios (`git commit -m 'Add: nuevo scraper pisos.com'`)
4. Push (`git push origin feature/nuevo-scraper`)
5. Crear Pull Request

## 📄 Licencia

MIT License - Ver `LICENSE` para detalles.

---

**Desarrollado con ❤️ por Arasmu** | **Dashboard Live**: [pisos.arasmu.net](https://pisos.arasmu.net)