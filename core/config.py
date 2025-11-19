from pathlib import Path
from datetime import datetime
import os
import json
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== RUTAS PRINCIPALES =====
BASE_DIR = Path(__file__).resolve().parent.parent

# Directorios
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output" 
TEMP_DIR = BASE_DIR / "temp"

# Crear directorios
for directorio in [UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR]:
    directorio.mkdir(exist_ok=True)

# ===== PLANTILLA EXCEL =====
def get_template_path():
    """Buscar plantilla Excel"""
    posibles_rutas = [
        BASE_DIR / "CEDULA LIBRO BLANCO (chatgpt).xlsx",
        BASE_DIR / "plantillas" / "CEDULA LIBRO BLANCO (chatgpt).xlsx",
    ]
    
    for ruta in posibles_rutas:
        if ruta.exists():
            logger.info(f"Plantilla encontrada: {ruta}")
            return ruta
    
    logger.warning("Plantilla no encontrada")
    return None

TEMPLATE_PATH = get_template_path()

# ===== CONFIGURACIÓN USUARIOS =====
USERS_FILE = BASE_DIR / "usuarios.json"

def load_users():
    """Cargar usuarios desde JSON"""
    if not USERS_FILE.exists():
        logger.error("Archivo de usuarios no encontrado")
        return {}
    
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            usuarios = json.load(f)
        
        # Convertir a diccionario
        usuarios_dict = {}
        for usuario in usuarios:
            username = usuario.get('usuario')
            if username:
                usuarios_dict[username] = {
                    'password': usuario.get('password', ''),
                    'nombre': usuario.get('nombre', username),
                    'nivel': usuario.get('nivel', 'usuario'),
                    'area': usuario.get('area', 'General')
                }
        
        logger.info(f"{len(usuarios_dict)} usuarios cargados")
        return usuarios_dict
        
    except Exception as e:
        logger.error(f"Error cargando usuarios: {e}")
        return {}

def authenticate_user(username, password):
    """Autenticar usuario"""
    try:
        usuarios = load_users()
        usuario = usuarios.get(username)
        
        if usuario and usuario.get('password') == password:
            logger.info(f"Usuario autenticado: {username}")
            return usuario
        else:
            logger.warning(f"Autenticación fallida: {username}")
            return None
    except Exception as e:
        logger.error(f"Error en autenticación: {e}")
        return None

# ===== UTILIDADES =====
def timestamp():
    """Generar timestamp para archivos"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def initialize_system():
    """Inicializar y verificar sistema"""
    logger.info("Inicializando sistema de contratos PEMEX")
    
    # Verificar directorios críticos
    for directorio in [UPLOAD_DIR, OUTPUT_DIR]:
        if not directorio.exists():
            logger.error(f"Directorio crítico no disponible: {directorio}")
            return False
    
    logger.info("Sistema inicializado correctamente")
    return True

SYSTEM_READY = initialize_system()