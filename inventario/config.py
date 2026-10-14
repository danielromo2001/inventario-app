import os
from pathlib import Path

VERSION = "1.1"  # subir al publicar cambios (y igualar AppVersion en instalador.iss)
try:
    from .build_info import COMPILACION  # lo escribe construir_exe.bat al empaquetar
except ImportError:
    COMPILACION = "desarrollo"
UMBRAL_STOCK_BAJO = 3  # avisar cuando queden 3 unidades o menos
MAX_NOMBRE = 120
MAX_PRECIO = 100_000_000
MAX_CANTIDAD = 100_000
COPIAS_A_CONSERVAR = 15  # copias de seguridad diarias que se guardan
NOMBRE_NEGOCIO = "ROMO El Rincón del Lubricante"
DIRECCION_NEGOCIO = "Carrera 4 #7-05, barrio San Luis"
TELEFONO_NEGOCIO = "300 299 3614"
NIT_NEGOCIO = "52783275-7"
CORREO_NEGOCIO = "marimo210581@gmail.com"
RUTA_LOGO = Path(__file__).parent / "assets" / "logo_marca.png"  # pon None para factura sin logo


def carpeta_datos() -> Path:
    """Carpeta local donde viven la base de datos y las facturas.

    Windows: C:\\Users\\<usuario>\\AppData\\Local\\InventarioLubricantes
    """
    base = os.environ.get("LOCALAPPDATA") or str(Path.home())
    ruta = Path(base) / "InventarioLubricantes"
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def carpeta_logs() -> Path:
    ruta = carpeta_datos() / "logs"
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta
