from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QButtonGroup, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
                               QPushButton, QStackedWidget, QVBoxLayout, QWidget)

from inventario import config
from .estilos import ASSETS
from .pagina_facturas import PaginaFacturas
from .pagina_inventario import PaginaInventario
from .pagina_venta import PaginaVenta
from .seguro import preguntar, seguro


class VentanaPrincipal(QMainWindow):
    def __init__(self, inv):
        super().__init__()
        self.inv = inv
        self.setWindowTitle(config.NOMBRE_NEGOCIO + " · Inventario")
        self.resize(1200, 760)

        self.pag_inventario = PaginaInventario(inv)
        self.pag_venta = PaginaVenta(inv)
        self.pag_facturas = PaginaFacturas(inv)
        self.paginas = [self.pag_inventario, self.pag_venta, self.pag_facturas]
        self.pag_inventario.datos_cambiados.connect(self.pag_venta.refrescar)
        self.pag_venta.venta_realizada.connect(self.pag_inventario.refrescar)

        self.stack = QStackedWidget()
        for p in self.paginas:
            self.stack.addWidget(p)
        self.stack.currentChanged.connect(lambda i: self.paginas[i].refrescar())

        # --- Barra lateral ---
        barra = QWidget(); barra.setObjectName("barra"); barra.setFixedWidth(240)
        capa_b = QVBoxLayout(barra)
        capa_b.setContentsMargins(16, 20, 16, 20); capa_b.setSpacing(6)
        logo = QLabel()
        pix = QPixmap(str(ASSETS / "logo_marca.png"))
        logo.setPixmap(pix.scaledToWidth(180, Qt.TransformationMode.SmoothTransformation))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        capa_b.addWidget(logo); capa_b.addSpacing(20)

        grupo = QButtonGroup(self)
        for i, texto in enumerate(["Inventario", "Nueva venta", "Facturas"]):
            b = QPushButton(texto); b.setObjectName("nav"); b.setCheckable(True)
            grupo.addButton(b, i)
            capa_b.addWidget(b)
            if i == 0:
                b.setChecked(True)
        grupo.idClicked.connect(self.stack.setCurrentIndex)
        capa_b.addStretch(1)

        contenido = QWidget(); contenido.setObjectName("contenido")
        capa_c = QVBoxLayout(contenido); capa_c.setContentsMargins(0, 0, 0, 0)
        capa_c.addWidget(self.stack)

        raiz = QWidget()
        capa = QHBoxLayout(raiz); capa.setContentsMargins(0, 0, 0, 0); capa.setSpacing(0)
        capa.addWidget(barra); capa.addWidget(contenido, 1)
        self.setCentralWidget(raiz)

        self.pag_inventario.refrescar()
        QTimer.singleShot(400, self._aviso_inicial)

    @seguro
    def _aviso_inicial(self, *_):
        bajos = self.inv.productos_stock_bajo()
        if bajos:
            lista = "\n".join(f"• {p['nombre']}: quedan {p['cantidad']}" for p in bajos[:15])
            QMessageBox.warning(self, "Productos por agotarse", lista)

    def closeEvent(self, evento):
        if self.pag_venta.hay_pendiente() and not preguntar(
                self, "Factura sin generar",
                "Hay productos en la factura en curso que aún no se han facturado.\n"
                "Si sales ahora se perderán (el inventario no cambia).\n¿Salir de todas formas?",
                si="Sí, salir", no="No, volver"):
            evento.ignore()
            return
        evento.accept()
