# 🏠 Dashboard Pisos Andorra

Dashboard interactivo para visualización de propiedades inmobiliarias en Andorra, con scrapers automatizados, base de datos PostgreSQL y interfaz web Streamlit.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

**🌍 Demo Live**: [pisos.arasmu.net](https://pisos.arasmu.net) | **IP Direct**: [161.97.147.142/pisos/](http://161.97.147.142/pisos/)

## 🎯 Estado Actual (Sep 2025)

✅ **Dashboard Completamente Funcional**  
✅ **1,683 Propiedades Cargadas**  
✅ **5 Scrapers Activos**  
✅ **Filtros Interactivos**  
✅ **Visualizaciones con Plotly**  
✅ **SSL & Domain pisos.arasmu.net**

## 🏗️ Arquitectura del Sistema

```
pisos-project/
├── 🗄️ Base de Datos (PostgreSQL)
│   └── properties_db (1,683 propiedades)
├── 🕷️ Scrapers Python
│   ├── pisosad_sql.py        # 35 propiedades (€127k-€9.5M)
│   ├── finquesmarques_sql.py # 59 propiedades  
│   ├── nouaire_sql.py        # 1,521 propiedades
│   ├── expofinques_sql.py    # 56 propiedades
│   └── claus_sql.py         # 12 propiedades
├── 📊 Dashboard (Streamlit)
│   └── streamlit_app.py     # Interfaz web interactiva
├── 🐳 Docker Containers
│   ├── pisos_streamlit_prod # Dashboard web
│   ├── pisos_scraper_prod   # Scrapers automáticos  
│   └── ecodisseny_dj_pg_db_1 # Base datos PostgreSQL
└── 🌐 Nginx Proxy
    └── Serve en /pisos/ con SSL
```

## 🎯 Scrapers Detallados

| Sitio Web | Scraper | Propiedades | Rango Precios | Estado |
|-----------|---------|-------------|---------------|--------|
| **pisos.ad** | `pisosad_sql.py` | **35** | €127k - €9.5M | ✅ **100% Funcional** |
| finquesmarca.com | `finquesmarques_sql.py` | 59 | €180k - €850k | ✅ Funcionando |
| nouaire.com | `nouaire_sql.py` | 1,521 | €85k - €2.1M | ✅ Funcionando |
| expofinques.com | `expofinques_sql.py` | 56 | €150k - €1.2M | ✅ Funcionando |
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