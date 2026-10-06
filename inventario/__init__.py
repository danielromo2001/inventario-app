"""Backend de control de inventario y facturación (100% local, SQLite + PDF)."""
from .servicio import Inventario, Carrito
from .errores import (
    InventarioError, ProductoNoEncontrado, ProductoDuplicado, StockInsuficiente,
    DatosInvalidos, CarritoVacio, ErrorBaseDatos, ErrorArchivo,
)

__all__ = [
    "Inventario", "Carrito", "InventarioError", "ProductoNoEncontrado", "ProductoDuplicado",
    "StockInsuficiente", "DatosInvalidos", "CarritoVacio", "ErrorBaseDatos", "ErrorArchivo",
]
