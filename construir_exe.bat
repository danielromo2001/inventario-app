@echo off
REM ============================================================
REM  Construye el programa para Windows: dist\ROMO Inventario\
REM  Ejecutar con doble clic o desde la terminal de VS Code
REM  (con el entorno virtual activo y despues de: pip install -r requirements.txt)
REM ============================================================
cd /d "%~dp0"

echo [1/3] Instalando PyInstaller...
python -m pip install --upgrade pyinstaller || goto :error

echo [2/3] Probando el backend antes de empaquetar...
python prueba_errores.py >nul 2>&1 || (echo Las pruebas fallaron. Revisa con: python prueba_errores.py & goto :error)

echo [3/3] Construyendo el programa...
python -m PyInstaller --noconfirm --clean --windowed ^
  --name "ROMO Inventario" ^
  --icon "inventario\assets\icono.ico" ^
  --add-data "inventario\assets;inventario\assets" ^
  main.py || goto :error

echo.
echo LISTO. El programa quedo en:  dist\ROMO Inventario\ROMO Inventario.exe
echo (Copia la carpeta completa "ROMO Inventario", no solo el .exe)
pause
exit /b 0

:error
echo.
echo Algo fallo. Copia el mensaje de arriba y envialo para revisarlo.
pause
exit /b 1
