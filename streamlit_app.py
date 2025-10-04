import streamlit as st
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import hashlib

# Configuración de la página
st.set_page_config(
    page_title="Propiedades en Andorra",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

import hashlib
import time

# Función que NUNCA usa caché 
def load_data_force_no_cache():
    """Carga los datos desde PostgreSQL y aplica todas las transformaciones"""
    try:
        # Configuración de la base de datos - usar variable de entorno
        import os
        DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://scraper_user:scraper_password@localhost:5432/properties_db")
        engine = create_engine(DATABASE_URL)
        
        # Cargar datos con filtros básicos
        query = """
        SELECT * FROM properties 
        WHERE price IS NOT NULL AND price > 0 
        ORDER BY timestamp DESC
        """
        
        df = pd.read_sql(query, engine)
        
        # Limpieza de datos
        if not df.empty:
            # Filtrar SOLO ubicaciones de Andorra país (usando todas las parroquias y ciudades)
            andorra_keywords = [
                'Andorra la Vella', 'Escaldes-Engordany', 'Encamp', 'Ordino', 
                'Canillo', 'La Massana', 'Sant Julia de Loria'
            ]
            
            # Crear filtro para Andorra (incluir variantes y subcategorías)
            andorra_pattern = '|'.join([
                r'andorra\s+la\s+vella',
                r'escaldes[-\s]*engordany', 
                r'encamp',
                r'ordino',
                r'canillo',
                r'la\s+massana',
                r'sant\s+julia'
            ])
            
            df = df[df['location'].str.contains(andorra_pattern, case=False, na=False, regex=True)]
            
            # Excluir explícitamente "Pas de la Casa" 
            pas_casa_pattern = r'pas\s+de\s+la\s+casa'
            df = df[~df['location'].str.contains(pas_casa_pattern, case=False, na=False, regex=True)]
            
            # FILTRO PRINCIPAL: Solo propiedades de VENTA entre 10,000€ y 450,000€
            df = df[(df['price'] >= 10000) & (df['price'] <= 450000)]
            
            # Convertir tipos de datos
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            df['rooms'] = pd.to_numeric(df['rooms'], errors='coerce')
            df['bathrooms'] = pd.to_numeric(df['bathrooms'], errors='coerce')
            df['surface'] = pd.to_numeric(df['surface'], errors='coerce')
            
            # Limpiar datos nulos
            df = df.dropna(subset=['price'])
            
            # ===== PROCESAMIENTO DE TIPOS DE PROPIEDAD DENTRO DEL CACHÉ =====
            def clean_title_cached(title):
                """Función de mapeo de títulos dentro del caché - v3.0 - Fixed cache invalidation"""
                if pd.isna(title):
                    return "Sin especificar"
                
                title_clean = str(title).strip()
                title_lower = title_clean.lower()
                
                # TÍTULOS EXACTOS (prioritario)
                if title_lower in ['piso', 'pis']:
                    return "Piso"
                elif title_lower in ['apartamento', 'apartament']:
                    return "Apartamento"
                elif title_lower in ['atico', 'àtic', 'ático']:
                    return "Ático"
                elif title_lower in ['bajo', 'baix', 'planta baja']:
                    return "Planta baja"
                elif title_lower in ['duplex', 'dúplex', 'dùplex']:
                    return "Duplex"
                elif title_lower in ['estudio', 'studio']:
                    return "Estudio"
                elif title_lower in ['chalet', 'xalet', 'casa']:
                    return "Casa/Chalet"
                elif title_lower in ['local comercial', 'oficina', 'despacho', 'despatx']:
                    return "Local comercial"
                elif title_lower in ['terreno', 'terreny', 'parcela', 'parcel']:
                    return "Terreno"
                elif title_lower in ['garaje', 'garatge', 'parking', 'parquing']:
                    return "Parking"
                
                # TÍTULOS DESCRIPTIVOS 
                elif ('pis ' in title_lower or title_lower.startswith('pis ') or ' pis ' in title_lower or 
                    'piso ' in title_lower or title_lower.startswith('piso ') or ' piso ' in title_lower):
                    return "Piso"
                elif 'apartament' in title_lower or 'apartment' in title_lower:
                    return "Apartamento"
                elif 'estudio' in title_lower or 'studio' in title_lower:
                    return "Estudio"
                elif 'duplex' in title_lower or 'dúplex' in title_lower or 'dùplex' in title_lower:
                    return "Duplex"
                elif ('atic' in title_lower or 'àtic' in title_lower or 'ático' in title_lower or 
                      'atico' in title_lower or 'penthouse' in title_lower):
                    return "Ático"
                elif 'planta baja' in title_lower or ' bajo ' in title_lower or 'baix' in title_lower:
                    return "Planta baja"
                elif ('xalet' in title_lower or 'chalet' in title_lower or 
                      (('casa ' in title_lower or title_lower.startswith('casa ')) and 'casa' not in ['escasa', 'ocasional'])):
                    return "Casa/Chalet"
                elif (('local' in title_lower and ('comercial' in title_lower or 'en venda' in title_lower or 'en venta' in title_lower)) or 
                      'oficina' in title_lower or 'despacho' in title_lower or 'despatx' in title_lower):
                    return "Local comercial"
                elif ('terreny' in title_lower or 'terreno' in title_lower or 'parcel' in title_lower or 
                      'solar' in title_lower or 'parcela' in title_lower):
                    return "Terreno"
                elif ('garatge' in title_lower or 'garaje' in title_lower or 'parking' in title_lower or 
                      'parquing' in title_lower or 'plaça' in title_lower or 'plaza' in title_lower):
                    return "Parking"
                else:
                    return "Otros"
            
            # ===== PROCESAMIENTO DE UBICACIONES DENTRO DEL CACHÉ =====
            def clean_location_cached(location):
                """Extrae el nombre principal de la población - dentro del caché"""
                if pd.isna(location):
                    return "Desconocida"
                
                main_locations = {
                    'Andorra la Vella': ['andorra la vella', 'andorra_la_vella'],
                    'Escaldes-Engordany': ['escaldes', 'engordany'],
                    'Encamp': ['encamp'],
                    'Ordino': ['ordino'],
                    'Canillo': ['canillo', 'tarter'],
                    'La Massana': ['massana'],
                    'Sant Julia de Loria': ['sant julia', 'julia']
                }
                
                location_lower = location.lower()
                for main_loc, keywords in main_locations.items():
                    if any(keyword in location_lower for keyword in keywords):
                        return main_loc
                
                return location
            
            # APLICAR TRANSFORMACIONES SIN CACHÉ
            print(f"🔄 Processing {len(df)} properties - Sept 27, 2025")
            df['tipo_propiedad'] = df['title'].apply(clean_title_cached)
            df['poblacion'] = df['location'].apply(clean_location_cached)
            
            # Debug: mostrar algunos ejemplos del mapeo
            sample_mappings = df[['title', 'tipo_propiedad']].head(10)
            print("📊 Sample mappings:")
            for _, row in sample_mappings.iterrows():
                print(f"  {row['title']} → {row['tipo_propiedad']}")
        
        return df
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return pd.DataFrame()

def main():
    # Configurar página con favicon
    st.set_page_config(
        page_title="Propiedades Andorra",
        page_icon="static/favicon.svg",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS optimizado para eliminar espacio pero preservar controles
    st.markdown("""
    <style>
    /* MAIN AREA - Dar espacio suficiente para el título */
    .main > div:first-child {padding-top: 1rem !important; margin-top: 0rem !important;}
    .block-container {padding-top: 1rem !important; margin-top: 0rem !important; padding-bottom: 1rem !important;}
    .st-emotion-cache-z5fcl4 {padding-top: 1rem !important;}
    .st-emotion-cache-18ewz0u {padding-top: 1rem !important;}
    .st-emotion-cache-1d391kg {padding-top: 1rem !important;}
    
    /* Asegurar que el contenedor principal tenga altura suficiente */
    .main .block-container {min-height: 100vh !important; overflow: visible !important;}
    
    /* SIDEBAR - Compactar contenido pero preservar controles */
    section[data-testid="stSidebar"] .stMarkdown {margin-top: 0rem !important;}
    section[data-testid="stSidebar"] .element-container {margin-top: 0rem !important;}
    .sidebar .sidebar-content {padding-top: 0.5rem !important;}
    
    /* Controles del sidebar - PRESERVAR */
    button[kind="header"] {visibility: visible !important;}
    [data-testid="collapsedControl"] {visibility: visible !important; display: block !important;}
    section[data-testid="stSidebar"] button {visibility: visible !important;}
    
    /* Logo y elementos del sidebar compactos */
    .sidebar img {margin-top: 0rem !important; margin-bottom: 0.5rem !important;}
    .sidebar h1, .sidebar h2, .sidebar h3 {margin-top: 0.2rem !important; margin-bottom: 0.5rem !important;}
    
    /* Header compacto - VISIBLE y estilizado */
    .main h1 {
        margin-top: 0.3rem !important; 
        margin-bottom: 0.5rem !important; 
        font-size: 1.1rem !important; 
        padding-top: 0.1rem !important;
        padding-bottom: 0.2rem !important;
        display: block !important;
        visibility: visible !important;
        color: #FAFAFA !important;
        font-weight: 500 !important;
        line-height: 1.2 !important;
        white-space: normal !important;
        overflow: visible !important;
        width: 100% !important;
    }
    
    /* Expandir compacto */
    .stExpander {margin: 0.2rem 0 !important;}
    .st-emotion-cache-1y4p8pa {margin: 0 !important; padding: 0.2rem !important;}
    
    /* Elementos de control siempre visibles */
    .st-emotion-cache-1rs6os {padding-top: 0.3rem !important;}
    
    /* Ocultar elementos innecesarios pero NO los controles del sidebar */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    # Header principal
    st.markdown("# 🏠 Propiedades Andorra • 10K-450K€ • Residenciales")
    
    # ===== LOGO DEL SIDEBAR PRIMERO DE TODO =====
    try:
        st.sidebar.image("static/logo_arasmu.svg", width=170)
    except:
        st.sidebar.markdown("**🏠 Arasmu**")  # Fallback text
    
    # Sistema automático info
    st.sidebar.markdown("---")
    st.sidebar.header("🤖 Sistema Automático")
    st.sidebar.markdown("""
    ✅ **Scrapers diarios a las 06:00**  
    """)
    
    # Info compacta (opcional - se puede ocultar/expandir)
    with st.expander("ℹ️ Info filtros", expanded=False):
        st.write("Propiedades residenciales en Andorra país • Por defecto: excluye Pas de la Casa, Arinsal y Bordes d'Envalira")
    
    # CLEAR ALL CACHES - Forzar actualización total
    st.cache_data.clear()
    
    # Cargar datos SIN CACHÉ NUNCA
    current_time = time.time()
    with st.spinner(f"Cargando datos FRESH (sin caché) - {current_time}..."):
        df = load_data_force_no_cache()
    
    if df.empty:
        st.error("No se pudieron cargar los datos o no hay propiedades que cumplan los criterios.")
        return
    
    # ===== SECCIÓN DE FILTROS =====
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filtros")
    
    # Las columnas 'tipo_propiedad' y 'poblacion' ya están procesadas en load_data()
    
    # Filtro múltiple de tipos de propiedad
    st.sidebar.subheader("🏠 Tipos de Propiedad")
    tipos_disponibles = sorted(df['tipo_propiedad'].unique())
    
    # Tipos residenciales por defecto (SOLO propiedades para vivir)
    tipos_residenciales = ['Piso', 'Apartamento', 'Estudio', 'Duplex', 'Planta baja', 'Ático']
    tipos_por_defecto = [tipo for tipo in tipos_residenciales if tipo in tipos_disponibles]
    
    tipos_seleccionados = st.sidebar.multiselect(
        "Selecciona tipos de propiedad:",
        options=tipos_disponibles,
        default=tipos_por_defecto,  # Incluye residenciales + terrenos + parking + locales
        help="Por defecto: propiedades residenciales (Piso, Apartamento, Estudio, Duplex, Planta baja, Ático)"
    )
    
    # Filtro múltiple de poblaciones - CORREGIDO: Excluir las 3 especiales por defecto
    st.sidebar.subheader("🏘️ Poblaciones")
    poblaciones_disponibles = sorted(df['poblacion'].unique())
    
    # POBLACIONES A EXCLUIR POR DEFECTO
    poblaciones_especiales = ['Pas de la Casa', 'Arinsal', 'Bordes d\'Envalira']
    poblaciones_por_defecto = [pob for pob in poblaciones_disponibles if pob not in poblaciones_especiales]
    
    poblaciones_seleccionadas = st.sidebar.multiselect(
        "Selecciona poblaciones:",
        options=poblaciones_disponibles,
        default=poblaciones_por_defecto,  # EXCLUYE Pas de la Casa, Arinsal y Bordes d'Envalira
        help="Por defecto: todas EXCEPTO Pas de la Casa, Arinsal y Bordes d'Envalira"
    )
    
    # Filtro por website
    websites = ['Todos'] + list(df['website'].unique())
    selected_website = st.sidebar.selectbox("Website", websites)
    
    # Filtro de precio para propiedades de venta
    st.sidebar.subheader("💰 Rango de Precio")
    st.sidebar.info("🏡 Propiedades de venta (10,000€ - 450,000€)")
    
    # Permitir ajustar el rango dentro del filtro de venta
    if not df.empty:
        current_min = max(10000, int(df['price'].min()))
        current_max = min(450000, int(df['price'].max()))
        
        min_price, max_price = st.sidebar.slider(
            "Ajustar rango de precio (€)",
            min_value=10000,
            max_value=450000,
            value=(current_min, current_max),
            step=5000,
            help="Solo propiedades de venta entre 10K€ y 450K€"
        )
        
        # Aplicar filtro de precio refinado
        filtered_df = df[(df['price'] >= min_price) & (df['price'] <= max_price)]
    else:
        min_price, max_price = 10000, 450000
        filtered_df = df
    
    # Filtro por habitaciones
    if filtered_df.empty:
        selected_rooms = 'Todas'
        surface_range = (0, 1000)
    else:
        if filtered_df['rooms'].notna().any():
            rooms_options = ['Todas'] + sorted([int(x) for x in filtered_df['rooms'].dropna().unique()])
            selected_rooms = st.sidebar.selectbox("Habitaciones", rooms_options)
        else:
            selected_rooms = 'Todas'
        
        # Filtro por superficie
        if filtered_df['surface'].notna().any():
            min_surface = int(filtered_df['surface'].min()) if filtered_df['surface'].notna().any() else 0
            max_surface = int(filtered_df['surface'].max()) if filtered_df['surface'].notna().any() else 1000
            surface_range = st.sidebar.slider(
                "Superficie (m²)",
                min_value=min_surface,
                max_value=max_surface,
                value=(min_surface, max_surface),
                step=10
            )
        else:
            surface_range = (0, 1000)
    
    # Aplicar filtros adicionales
    if not filtered_df.empty:
        # Filtro de tipos de propiedad
        if tipos_seleccionados:
            filtered_df = filtered_df[filtered_df['tipo_propiedad'].isin(tipos_seleccionados)]
        
        # Filtro de poblaciones
        if poblaciones_seleccionadas:
            filtered_df = filtered_df[filtered_df['poblacion'].isin(poblaciones_seleccionadas)]
        
        # Filtro por website
        if selected_website != 'Todos':
            filtered_df = filtered_df[filtered_df['website'] == selected_website]
        
        # Filtro de habitaciones
        if selected_rooms != 'Todas':
            filtered_df = filtered_df[filtered_df['rooms'] == selected_rooms]
        
        # Filtro de superficie
        if df['surface'].notna().any():
            filtered_df = filtered_df[
                (filtered_df['surface'] >= surface_range[0]) & 
                (filtered_df['surface'] <= surface_range[1])
            ]
    
    # Métricas principales
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Propiedades", len(filtered_df))
    
    with col2:
        tipos_unicos = len(filtered_df['tipo_propiedad'].unique())
        st.metric("Tipos Diferentes", tipos_unicos)
    
    with col3:
        avg_price = filtered_df['price'].mean()
        st.metric("Precio Promedio", f"{avg_price:,.0f}€")
    
    with col4:
        min_price_prop = filtered_df['price'].min()
        st.metric("Precio Mínimo", f"{min_price_prop:,.0f}€")
    
    with col5:
        max_price_prop = filtered_df['price'].max()
        st.metric("Precio Máximo", f"{max_price_prop:,.0f}€")
    
    # Gráficos principales (solo 2 más importantes)
    if len(filtered_df) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribución de precios
            fig_price = px.histogram(
                filtered_df, 
                x='price', 
                nbins=15,
                title="📊 Distribución de Precios",
                labels={'price': 'Precio (€)', 'count': 'Cantidad'}
            )
            fig_price.update_layout(height=350)
            st.plotly_chart(fig_price, use_container_width=True)
        
        with col2:
            # Precio promedio por población
            precio_por_poblacion = filtered_df.groupby('poblacion')['price'].mean().sort_values(ascending=False)
            fig_precio_poblacion = px.bar(
                x=precio_por_poblacion.values,
                y=precio_por_poblacion.index,
                orientation='h',
                title="💰 Precio Promedio por Población",
                labels={'x': 'Precio promedio (€)', 'y': 'Población'},
                color=precio_por_poblacion.values,
                color_continuous_scale='viridis'
            )
            fig_precio_poblacion.update_layout(height=350)
            st.plotly_chart(fig_precio_poblacion, use_container_width=True)

    
    # Tabla de propiedades
    st.header("📋 Lista de Propiedades")
    st.markdown("*Ordenadas por precio de menor a mayor* 💸")
    
    if len(filtered_df) > 0:
        # Ordenar por precio ascendente (más baratas primero)
        filtered_df_sorted = filtered_df.sort_values('price', ascending=True)
        
        # Seleccionar columnas relevantes para mostrar
        display_columns = ['tipo_propiedad', 'price', 'rooms', 'bathrooms', 'surface', 'poblacion', 'location', 'website', 'url']
        display_df = filtered_df_sorted[display_columns].copy()
        
        # Formatear el precio
        display_df['price'] = display_df['price'].apply(lambda x: f"{x:,.0f}€")
        
        # Renombrar columnas
        column_names = {
            'tipo_propiedad': 'Tipo',
            'price': 'Precio',
            'rooms': 'Habitaciones',
            'bathrooms': 'Baños',
            'surface': 'Superficie (m²)',
            'poblacion': 'Población',
            'location': 'Ubicación Completa',
            'website': 'Website',
            'url': 'URL'
        }
        display_df = display_df.rename(columns=column_names)
        
        # Mostrar tabla con paginación
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "URL": st.column_config.LinkColumn(
                    "URL",
                    help="Enlace a la propiedad",
                    display_text="Ver propiedad"
                )
            }
        )
        
        # Opción para descargar datos
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="💾 Descargar datos como CSV",
            data=csv,
            file_name=f"propiedades_andorra_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No se encontraron propiedades con los filtros seleccionados.")
    
    # Información adicional
    with st.expander("ℹ️ Información sobre los datos"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"""
            **📊 Estadísticas**
            - Total propiedades en BD: {len(df)}
            - Propiedades mostradas: {len(filtered_df)}
            - Tipos disponibles: {len(df['tipo_propiedad'].unique())}
            - Poblaciones: {len(df['poblacion'].unique())}
            """)
            
        with col2:
            st.write(f"""
            **🎯 Filtros Aplicados**
            - Solo Andorra país (sin Pas de la Casa)
            - Precio: 10,000€ - 450,000€
            - Por defecto: Propiedades residenciales
            - Fuentes: {', '.join(df['website'].unique())}
            """)
    
    # Footer compacto con branding
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 10px; color: #888; font-size: 0.85em;">
        <span>🏠 <strong>Arasmu</strong> Dashboard • 
        <a href="https://github.com/Mulastone" target="_blank" style="color: #1f77b4; text-decoration: none;">GitHub</a></span>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()