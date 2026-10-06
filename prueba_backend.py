"""Prueba rápida de todo el backend. Ejecutar: python prueba_backend.py"""
import tempfile
from inventario import *

inv = Inventario(tempfile.mkdtemp())
aceite = inv.crear_producto("Aceite 20W-50 Carro 1L", 32000, 10)
filtro = inv.crear_producto("Filtro de aceite moto", 18000, 4)
inv.crear_producto("Refrigerante verde 1G", 25000, 2)

try: inv.crear_producto("aceite 20w-50 carro 1l", 1, 1)
except ProductoDuplicado as e: print("OK duplicado:", e)

inv.modificar_producto(aceite["id"], "Aceite 20W-50 Carro 1L", 34000, 10)
print("Stock bajo:", [p["nombre"] for p in inv.productos_stock_bajo()])

c = Carrito(); c.agregar(aceite["id"], 2); c.agregar(filtro["id"], 2)
print("Total previo:", inv.total_carrito(c))
r = inv.confirmar_venta(c, "Juan Pérez")
print("Venta:", r["numero"], r["total"], r["pdf_ruta"])
print("Alertas tras venta:", [(p["nombre"], p["cantidad"]) for p in r["alertas_stock_bajo"]])

c2 = Carrito(); c2.agregar(filtro["id"], 5)
try: inv.confirmar_venta(c2)
except StockInsuficiente as e: print("OK sin stock:", e)
assert inv.obtener_producto(filtro["id"])["cantidad"] == 2  # no se descontó nada

inv.eliminar_producto(filtro["id"])
print("Facturas conservadas:", len(inv.listar_facturas()))

# Validación del carrito: stock 2, intento agregar 4 y luego 2+1
x = inv.crear_producto("Desengrasante 1L", 15000, 2)
c3 = Carrito()
try: inv.agregar_al_carrito(c3, x["id"], 4)
except StockInsuficiente as e: print("OK carrito 4 de 2:", e)
inv.agregar_al_carrito(c3, x["id"], 2)
try: inv.agregar_al_carrito(c3, x["id"], 1)
except StockInsuficiente as e: print("OK carrito 2+1 de 2:", e)
