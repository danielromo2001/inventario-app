"""Punto de entrada: python main.py"""
import logging
import sys
from logging.handlers import RotatingFileHandler

from PySide6.QtCore import QLockFile
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from inventario import Inventario, InventarioError, config
from ui.estilos import ASSETS, QSS, cargar_fuente
from ui.ventana import VentanaPrincipal

log = logging.getLogger("app")


def configurar_registro():
    """Guarda un registro técnico para soporte; nunca impide que la app arranque."""
    try:
        ruta = config.carpeta_logs() / "app.log"
        h = RotatingFileHandler(ruta, maxBytes=500_000, backupCount=3, encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logging.basicConfig(level=logging.INFO, handlers=[h])
        return ruta
    except OSError:
        logging.basicConfig(level=logging.INFO)
        return None


def instalar_red_de_seguridad(ruta_log):
    """Último recurso: cualquier error no previsto se explica en lugar de cerrar la app en silencio."""
    def gancho(tipo, valor, tb):
        if issubclass(tipo, KeyboardInterrupt):
            return sys.__excepthook__(tipo, valor, tb)
        log.critical("Error no controlado", exc_info=(tipo, valor, tb))
        try:
            QMessageBox.critical(
                None, "Ocurrió un error inesperado",
                "Algo salió mal, pero tus datos están a salvo.\n\nSi el problema se repite, cierra y "
                "abre la aplicación de nuevo y avisa al soporte.\n"
                + (f"\nDetalle técnico guardado en:\n{ruta_log}" if ruta_log else ""))
        except Exception:
            pass
    sys.excepthook = gancho


def error_fatal(texto):
    QMessageBox.critical(None, "No se pudo iniciar la aplicación", texto)
    return 1


def main() -> int:
    ruta_log = configurar_registro()
    if sys.platform == "win32":  # para que la barra de tareas muestre el logo de ROMO y no el de Python
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("romo.inventario.lubricantes")
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(ASSETS / "icono.png")))
    app.setStyle("Fusion")  # aspecto uniforme en cualquier Windows
    cargar_fuente(app)
    app.setStyleSheet(QSS)
    instalar_red_de_seguridad(ruta_log)

    try:
        carpeta = config.carpeta_datos()
    except OSError as e:
        return error_fatal(f"No se pudo crear la carpeta de datos ({e.strerror or e}). "
                           "Revisa los permisos de tu usuario de Windows.")

    # Una sola ventana a la vez: dos copias abiertas podrían pelear por la misma base de datos.
    cerrojo = QLockFile(str(carpeta / "inventario.lock"))
    if not cerrojo.tryLock(300):
        QMessageBox.information(None, "Ya está abierta",
                                "La aplicación ya está abierta. Búscala en la barra de tareas.")
        return 0

    try:
        inv = Inventario(carpeta)  # datos en %LOCALAPPDATA%\\InventarioLubricantes
    except InventarioError as e:
        cerrojo.unlock()
        return error_fatal(str(e))

    try:
        inv.respaldar()
    except InventarioError:
        log.warning("No se pudo crear la copia de seguridad de hoy", exc_info=True)

    ventana = VentanaPrincipal(inv)
    ventana.show()
    codigo = app.exec()
    inv.cerrar()
    cerrojo.unlock()
    return codigo


if __name__ == "__main__":
    sys.exit(main())
