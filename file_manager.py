from pathlib import Path
from core.config import OUTPUT_DIR, timestamp

def crear_carpetas_contrato(usuario, numero_contrato):
    """
    Crea la estructura de carpetas por usuario y contrato.
    """
    base = Path(OUTPUT_DIR) / usuario / "CONTRATOS" / numero_contrato
    cedula_dir = base / "CEDULA"
    anexos_dir = base / "ANEXOS"
    soportes_dir = base / "SOPORTES_FISICOS"

    for carpeta in [cedula_dir, anexos_dir, soportes_dir]:
        carpeta.mkdir(parents=True, exist_ok=True)

    return {
        "base": base,
        "cedula": cedula_dir,
        "anexos": anexos_dir,
        "soportes": soportes_dir
    }

def guardar_archivo(file_buffer, destino: Path):
    """
    Guarda un archivo subido por Streamlit en la ruta destino.
    """
    with open(destino, "wb") as f:
        f.write(file_buffer.getbuffer())
