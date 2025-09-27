# 🏠 Scraper Dashboard Andorra

Dashboard interactivo para visualización de propiedades inmobiliarias en Andorra, con scrapers automatizados y base de datos PostgreSQL.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**🌍 Demo Live**: [scraper.arasmu.net](https://scraper.arasmu.net)

## 🏗️ Estructura del Proyecto

```
scraper-project/
├── src/
│   ├── database/           # Configuración y operaciones de BD
│   │   ├── connection.py   # Conexión a PostgreSQL
│   │   └── operations.py   # CRUD operations
│   ├── models/
│   │   └── property.py     # Modelo de datos Property
│   ├── scrapers/           # Scrapers principales
│   │   ├── finquesmarques_sql.py  # 59 propiedades
│   │   ├── nouaire_sql.py         # 1,521 propiedades
│   │   ├── expofinques_sql.py     # 56 propiedades
│   │   ├── claus_sql.py          # 12 propiedades (7claus.com)
│   │   └── runner.py             # Ejecutor de todos los scrapers
│   └── utils/
│       └── text_cleaner.py # Limpieza y normalización de texto
├── docker/
│   └── Dockerfile          # Imagen Docker del scraper
├── antic/                  # Archivos obsoletos/backup
├── docker-compose.yml      # PostgreSQL + Scraper
├── requirements.txt        # Dependencias Python
└── .gitignore             # Exclusiones Git
```

## 🎯 Scrapers Activos

| Sitio Web            | Scraper                 | Propiedades | Estado         |
| -------------------- | ----------------------- | ----------- | -------------- |
| www.finquesmarca.com | `finquesmarques_sql.py` | 59          | ✅ Funcionando |
| www.nouaire.com      | `nouaire_sql.py`        | 1,521       | ✅ Funcionando |
| www.expofinques.com  | `expofinques_sql.py`    | 56          | ✅ Funcionando |
| www.7claus.com       | `claus_sql.py`          | 12          | ✅ Funcionando |

**Total: 1,648 propiedades**

## 🚀 Uso

### Configuración inicial

```bash
# Clonar y setup
git clone <repo>
cd scraper-project

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o .venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Iniciar PostgreSQL
docker-compose up -d postgres
```

### Ejecutar scrapers

```bash
# Ejecutar todos los scrapers
python -m src.scrapers.runner

# Ejecutar scraper específico
python -m src.scrapers.finquesmarques_sql
python -m src.scrapers.nouaire_sql
python -m src.scrapers.expofinques_sql
python -m src.scrapers.claus_sql
```

## 🗄️ Base de Datos

### Esquema de tabla `properties`

```sql
CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    price INTEGER,
    rooms INTEGER,
    bathrooms INTEGER,
    surface INTEGER,
    timestamp TIMESTAMP,
    website VARCHAR(255),
    title TEXT,
    reference VARCHAR(100),
    operation VARCHAR(50),
    location VARCHAR(255),
    address TEXT,
    url TEXT UNIQUE
);
```

### Consultas útiles

```sql
-- Resumen por website
SELECT website, COUNT(*) as total
FROM properties
GROUP BY website
ORDER BY total DESC;

-- Propiedades más caras
SELECT title, price, website
FROM properties
WHERE price > 0
ORDER BY price DESC
LIMIT 10;

-- Estadísticas por ubicación
SELECT location, COUNT(*) as total, AVG(price) as precio_promedio
FROM properties
WHERE location IS NOT NULL
GROUP BY location
ORDER BY total DESC;
```

## 🐳 Docker

### Servicios disponibles

- **postgres**: Base de datos PostgreSQL 14
- **scraper**: Aplicación scraper (opcional)

### Variables de entorno

```bash
POSTGRES_USER=scraper_user
POSTGRES_PASSWORD=scraper_password
POSTGRES_DB=properties_db
```

## 🔧 Desarrollo

### Añadir nuevo scraper

1. Crear archivo en `src/scrapers/nuevo_scraper.py`
2. Implementar clase con método `run()`
3. Añadir al runner en `src/scrapers/runner.py`
4. Usar `PropertyRepository` para guardar datos

### Estructura mínima de scraper

```python
from ..database.operations import PropertyRepository
from ..database.connection import create_tables

class NuevoScraper:
    def __init__(self):
        self.website = "www.ejemplo.com"

    def run(self):
        create_tables()
        property_repo = PropertyRepository()
        # ... lógica de scraping ...
        property_repo.save_property(data)
```

## 📁 Archivos en `antic/`

- Versiones anteriores de scrapers
- Scripts de prueba y validación obsoletos
- Archivos de configuración corruptos
- Backups y código experimental

## 🤝 Contribuir

1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/nuevo-scraper`)
3. Commit cambios (`git commit -am 'Add nuevo scraper'`)
4. Push a la rama (`git push origin feature/nuevo-scraper`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo licencia MIT.
