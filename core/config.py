# core/config.py
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

# Directorios principales (MANTENIDOS PARA ARCHIVOS PERMANENTES)
UPLOAD_DIR = BASE_DIR / "uploads"           # Archivos temporales de upload
OUTPUT_DIR = BASE_DIR / "output"           # Archivos generados (Excel, etc.)
TEMP_DIR = BASE_DIR / "temp"               # Archivos temporales
DATA_DIR = BASE_DIR / "data"               # Datos permanentes locales
BACKUP_DIR = BASE_DIR / "backups"          # Backups de seguridad

# Crear directorios principales
for directorio in [UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR, DATA_DIR, BACKUP_DIR]:
    directorio.mkdir(exist_ok=True)

# ===== CONFIGURACIÓN USUARIOS =====
USERS_FILE = DATA_DIR / "usuarios.json"

def load_users():
    """Cargar usuarios desde JSON (LOCAL PERMANENTE)"""
    if not USERS_FILE.exists():
        logger.error("Archivo de usuarios no encontrado")
        
        # Crear archivo de usuarios por defecto si no existe
        usuarios_por_defecto = [
            {
                "usuario": "ADMIN",
                "password": "admin123",
                "nombre": "ADMINISTRADOR",
                "nivel": "admin",
                "area": "SISTEMAS"
            }
        ]
        
        try:
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(usuarios_por_defecto, f, ensure_ascii=False, indent=2)
            logger.info("Archivo de usuarios creado con usuario por defecto")
        except Exception as e:
            logger.error(f"Error creando archivo de usuarios: {e}")
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
    """Autenticar usuario (LOCAL PERMANENTE)"""
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

def crear_usuario(usuario_data):
    """Crear nuevo usuario (LOCAL PERMANENTE)"""
    try:
        usuarios = load_users()
        
        # Convertir de dict a lista para agregar
        usuarios_lista = []
        for user_id, user_info in usuarios.items():
            usuarios_lista.append({
                "usuario": user_id,
                "password": user_info['password'],
                "nombre": user_info['nombre'],
                "nivel": user_info['nivel'],
                "area": user_info['area']
            })
        
        # Agregar nuevo usuario
        usuarios_lista.append(usuario_data)
        
        # Guardar
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(usuarios_lista, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Usuario creado: {usuario_data['usuario']}")
        return True
        
    except Exception as e:
        logger.error(f"Error creando usuario: {e}")
        return False

# ===== CONFIGURACIÓN ANEXOS =====
ANEXOS_FILE = DATA_DIR / "anexos_base.json"

def cargar_anexos_conocidos():
    """Cargar anexos conocidos (LOCAL PERMANENTE)"""
    anexos_base = [
        "A", "B", "B-1", "C", "CN", "E", "F", "I", "SSPA", "PACMA",
        "AP", "MMRDD", "GNR", "PUE", "BDE", "GARANTÍAS", "FORMA", "DT-9",
        "II", "IV", "O"
    ]
    
    if not ANEXOS_FILE.exists():
        # Crear archivo con anexos base
        try:
            with open(ANEXOS_FILE, 'w', encoding='utf-8') as f:
                json.dump(sorted(set(anexos_base)), f, ensure_ascii=False, indent=2)
            logger.info("Archivo de anexos creado")
        except Exception as e:
            logger.error(f"Error creando archivo de anexos: {e}")
            return anexos_base
    
    try:
        with open(ANEXOS_FILE, 'r', encoding='utf-8') as f:
            anexos = json.load(f)
        logger.info(f"{len(anexos)} anexos conocidos cargados")
        return anexos
    except Exception as e:
        logger.error(f"Error cargando anexos: {e}")
        return anexos_base

def guardar_anexos_conocidos(anexos):
    """Guardar anexos conocidos (LOCAL PERMANENTE)"""
    try:
        with open(ANEXOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(sorted(set(anexos)), f, ensure_ascii=False, indent=2)
        logger.info(f"Anexos guardados: {len(anexos)} elementos")
        return True
    except Exception as e:
        logger.error(f"Error guardando anexos: {e}")
        return False

# ===== PLANTILLA EXCEL =====
def get_template_path():
    """Buscar plantilla Excel (LOCAL PERMANENTE)"""
    posibles_rutas = [
        BASE_DIR / "CEDULA LIBRO BLANCO (chatgpt).xlsx",
        BASE_DIR / "plantillas" / "CEDULA LIBRO BLANCO (chatgpt).xlsx",
        DATA_DIR / "plantillas" / "CEDULA LIBRO BLANCO (chatgpt).xlsx",
    ]
    
    for ruta in posibles_rutas:
        if ruta.exists():
            logger.info(f"Plantilla encontrada: {ruta}")
            return ruta
    
    logger.warning("Plantilla no encontrada")
    return None

TEMPLATE_PATH = get_template_path()

# ===== CONFIGURACIÓN BACKUPS =====
def crear_backup_contrato(contrato_data, archivos_data, usuario):
    """Crear backup local de contrato (LOCAL PERMANENTE)"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"backup_contrato_{timestamp}.json"
        
        backup_data = {
            "timestamp": timestamp,
            "usuario": usuario,
            "metadata": contrato_data,
            "archivos": {
                "principal": archivos_data.get('principal', {}).get('name', '') if archivos_data.get('principal') else '',
                "anexos_count": len(archivos_data.get('anexos', [])),
                "cedulas_count": len(archivos_data.get('cedulas', [])),
                "soportes_count": len(archivos_data.get('soportes', []))
            }
        }
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Backup creado: {backup_file}")
        return backup_file
        
    except Exception as e:
        logger.error(f"Error creando backup: {e}")
        return None

def listar_backups():
    """Listar backups disponibles (LOCAL PERMANENTE)"""
    try:
        backups = sorted(BACKUP_DIR.glob("backup_contrato_*.json"))
        return backups
    except Exception as e:
        logger.error(f"Error listando backups: {e}")
        return []

# ===== CONFIGURACIÓN LOGS =====
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

def setup_file_logging():
    """Configurar logging a archivo (LOCAL PERMANENTE)"""
    log_file = LOG_DIR / f"system_{datetime.now().strftime('%Y%m')}.log"
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    return log_file

# Configurar file logging
LOG_FILE = setup_file_logging()

# ===== UTILIDADES =====
def timestamp():
    """Generar timestamp para archivos"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def get_user_data_dir(usuario):
    """Obtener directorio de datos del usuario (LOCAL PERMANENTE)"""
    user_dir = DATA_DIR / "usuarios" / usuario.upper()
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir

def initialize_system():
    """Inicializar y verificar sistema"""
    logger.info("=== INICIALIZANDO SISTEMA DE CONTRATOS PEMEX ===")
    
    # Verificar directorios críticos
    directorios_criticos = [DATA_DIR, BACKUP_DIR, LOG_DIR]
    for directorio in directorios_criticos:
        if not directorio.exists():
            logger.error(f"Directorio crítico no disponible: {directorio}")
            return False
    
    # Verificar archivos críticos
    if not USERS_FILE.exists():
        logger.warning("Archivo de usuarios no encontrado - se creará automáticamente")
    
    # Cargar configuración inicial
    usuarios_count = len(load_users())
    anexos_count = len(cargar_anexos_conocidos())
    
    logger.info(f"✅ Sistema inicializado correctamente")
    logger.info(f"📊 Usuarios cargados: {usuarios_count}")
    logger.info(f"📊 Anexos conocidos: {anexos_count}")
    logger.info(f"🗄️ Directorio datos: {DATA_DIR}")
    logger.info(f"📁 Directorio backups: {BACKUP_DIR}")
    logger.info(f"📝 Log file: {LOG_FILE}")
    
    return True

SYSTEM_READY = initialize_system()

# ===== CONFIGURACIÓN POSTGRESQL =====
def get_postgresql_config():
    """Obtener configuración de PostgreSQL"""
    return {
        'enabled': True,
        'max_file_size_gb': 4,  # 4TB teórico, práctico 4GB
        'supported_formats': ['pdf', 'doc', 'docx', 'xlsx', 'jpg', 'png'],
        'backup_local': True  # Mantener backups locales además de PostgreSQL
    }

POSTGRESQL_CONFIG = get_postgresql_config()
