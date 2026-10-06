import functools
import logging
from PySide6.QtWidgets import QMessageBox
from inventario import InventarioError

log = logging.getLogger("ui")


def seguro(f):
    """Muestra un mensaje claro si algo falla dentro de una acción, en vez de cerrar o congelar la app."""
    @functools.wraps(f)
    def envoltura(self, *a, **k):
        try:
            return f(self, *a, **k)
        except InventarioError as e:
            QMessageBox.warning(self, "No se pudo completar la acción", str(e))
        except Exception:
            log.exception("Error inesperado en %s", f.__name__)
            QMessageBox.critical(
                self, "Ocurrió un error inesperado",
                "Algo salió mal con esta acción, pero la aplicación sigue funcionando y tus datos "
                "están a salvo. Inténtalo de nuevo; si se repite, avisa al soporte (el detalle "
                "quedó guardado en el registro de la aplicación).")
    return envoltura


def preguntar(parent, titulo, texto, si="Sí", no="No") -> bool:
    """Confirmación con el botón seguro (No) como predeterminado."""
    caja = QMessageBox(QMessageBox.Icon.Warning, titulo, texto,
                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, parent)
    caja.button(QMessageBox.StandardButton.Yes).setText(si)
    caja.button(QMessageBox.StandardButton.No).setText(no)
    caja.setDefaultButton(QMessageBox.StandardButton.No)
    return caja.exec() == QMessageBox.StandardButton.Yes
