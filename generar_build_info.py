"""Lo usa construir_exe.bat: deja grabada en el programa la fecha y hora en que se construyó."""
import datetime
import pathlib

destino = pathlib.Path(__file__).parent / "inventario" / "build_info.py"
destino.write_text(f'COMPILACION = "{datetime.datetime.now():%Y-%m-%d %H:%M}"\n', encoding="utf-8")
print("Construccion:", destino.read_text().strip())
