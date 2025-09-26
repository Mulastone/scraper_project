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
    Convierte un valor a entero, retorna 0 si no es posible
    """
    try:
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

def convertir_a_entero(texto):
    """
    Convierte texto a entero
    """
    if not texto:
        return 0
    
    try:
        return int(float(re.sub(r'[^\d.]', '', str(texto))))
    except ValueError:
        return 0