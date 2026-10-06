class InventarioError(Exception):
    """Base de todos los errores de negocio: su mensaje siempre es apto para mostrar al usuario."""

class ProductoNoEncontrado(InventarioError): pass
class ProductoDuplicado(InventarioError): pass
class StockInsuficiente(InventarioError): pass
class DatosInvalidos(InventarioError): pass
class CarritoVacio(InventarioError): pass
class ErrorBaseDatos(InventarioError): pass
class ErrorArchivo(InventarioError): pass
