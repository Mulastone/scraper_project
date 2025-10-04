import re
import unicodedata

def limpiar_texto(texto):
    """
    Limpia el texto eliminando caracteres especiales y normalizando
    """
    if not texto or texto == 'N/A':
        return 'N/A'
    
    # Normalizar unicode
    texto = unicodedata.normalize('NFKD', str(texto))
    
    # Remover caracteres especiales y múltiples espacios
    texto = re.sub(r'[^\w\s.,€/-]', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    
    return texto.strip()

def extraer_titulo(texto):
    """
    Extrae el título de la propiedad
    """
    if 'en ' in texto:
        return texto.split('en ')[0].strip()
    return texto

def extraer_direccion(texto):
    """
    Extrae la dirección de la propiedad
    """
    if 'en ' in texto:
        return texto.split('en ', 1)[1].strip()
    return 'N/A'

def extraer_precio(texto):
    """
    Extrae el precio numérico del texto
    """
    if not texto:
        return 0
    
    # Remover caracteres no numéricos excepto punto y coma
    precio_limpio = re.sub(r'[^\d.,]', '', str(texto))
    
    # Si hay puntos y comas, asumir formato europeo (1.234,56)
    if '.' in precio_limpio and ',' in precio_limpio:
        # Formato: 1.234.567,89 -> 1234567.89
        precio_limpio = precio_limpio.replace('.', '').replace(',', '.')
    elif '.' in precio_limpio:
        # Si solo hay puntos, podrían ser separadores de miles o decimales
        partes = precio_limpio.split('.')
        if len(partes) == 2 and len(partes[1]) <= 2:
            # Probablemente decimal: 1234.50
            pass
        else:
            # Probablemente separador de miles: 1.234.567
            precio_limpio = precio_limpio.replace('.', '')
    elif ',' in precio_limpio:
        # Comma como decimal: 1234,50
        precio_limpio = precio_limpio.replace(',', '.')
    
    try:
        return float(precio_limpio)
    except ValueError:
        return 0

def convertir_a_entero_o_na(valor):
    """
    Convierte un valor a entero o retorna 'N/A'
    """
    try:
        # Extraer solo números del texto
        numeros = re.findall(r'\d+', str(valor))
        return int(numeros[0]) if numeros else 'N/A'
    except (ValueError, IndexError):
        return 'N/A'

def convertir_a_entero(valor):
    """
    Convierte un valor a entero o float, retorna 0 si no es posible
    """
    try:
        # Buscar números decimales primero (con coma o punto)
        decimal_match = re.search(r'(\d+(?:[.,]\d+)?)', str(valor))
        if decimal_match:
            # Convertir coma a punto para decimales
            numero_str = decimal_match.group(1).replace(',', '.')
            return float(numero_str)
        
        # Si no hay decimales, buscar solo enteros
        numeros = re.findall(r'\d+', str(valor))
        return int(numeros[0]) if numeros else 0
    except (ValueError, IndexError):
        return 0

def convertir_a_entero_limpiar(valor):
    """
    Convierte un valor a entero removiendo texto como 'm2', 'm²'
    """
    try:
        valor_limpio = str(valor).replace('m2', '').replace('m²', '').replace('m', '').strip()
        numeros = re.findall(r'\d+', valor_limpio)
        return int(numeros[0]) if numeros else 0
    except (ValueError, IndexError):
        return 0

def modificar_operacion(operacion):
    """
    Modifica y limpia el texto de operación
    """
    operacion = str(operacion).lower()
    if 'venta' in operacion or 'vendre' in operacion or 'sell' in operacion:
        return 'Venta'
    elif 'alquiler' in operacion or 'lloguer' in operacion or 'rent' in operacion:
        return 'Alquiler'
    return limpiar_texto(operacion).title()



def detectar_pas_de_la_casa(texto):
    """
    Detecta si el texto contiene referencias a Pas de la Casa
    Retorna True si encuentra referencias, False si no
    """
    if not texto:
        return False
    
    # Normalizar texto para búsqueda case-insensitive
    texto_normalizado = texto.lower()
    
    # Patrones para detectar SOLO referencias específicas a Pas de la Casa
    patrones = [
        r'pas\s+de\s+la\s+casa',  # "Pas de la Casa" (principal)
        r'pas\s+casa',            # "Pas Casa" (abreviado)
        r'paso\s+de\s+la\s+casa', # "Paso de la Casa" (español)
        r'paso\s+casa',           # "Paso Casa" (español abreviado)
        r'pas\s+de\s+casa',       # "Pas de Casa" (sin "la")
    ]
    
    # Buscar cualquiera de los patrones
    for patron in patrones:
        if re.search(patron, texto_normalizado):
            return True
    
    return False

def detectar_arinsal(texto):
    """
    Detecta si el texto contiene referencias específicas a Arinsal
    Retorna True si encuentra referencias, False si no
    """
    if not texto:
        return False
    
    # Normalizar texto para búsqueda case-insensitive
    texto_normalizado = texto.lower()
    
    # Patrones para detectar referencias específicas a Arinsal
    patrones = [
        r'\barinsal\b',           # "Arinsal" como palabra completa
        r'estació\s+arinsal',     # "estació Arinsal"
        r'estacion\s+arinsal',    # "estacion Arinsal"
        r'pistes\s+arinsal',      # "pistes Arinsal"
        r'pistas\s+arinsal',      # "pistas Arinsal"
    ]
    
    # Buscar cualquiera de los patrones
    for patron in patrones:
        if re.search(patron, texto_normalizado):
            return True
    
    return False

def detectar_bordes(texto):
    """
    Detecta si el texto contiene referencias específicas a Bordes d'Envalira
    Retorna True si encuentra referencias, False si no
    """
    if not texto:
        return False
    
    # Normalizar texto para búsqueda case-insensitive
    texto_normalizado = texto.lower()
    
    # Patrones para detectar referencias específicas a Bordes
    patrones = [
        r"bordes\s+d[\'']?envalira",  # "Bordes d'Envalira"
        r'bordes\s+de\s+envalira',    # "Bordes de Envalira"
        r'bordes\s+envalira',         # "Bordes Envalira"
        r'\bbordes\b',                # "Bordes" como palabra completa
    ]
    
    # Buscar cualquiera de los patrones
    for patron in patrones:
        if re.search(patron, texto_normalizado):
            return True
    
    return False