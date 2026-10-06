; Instalador opcional (requiere Inno Setup, gratis: jrsoftware.org/isinfo.php)
; Uso: construir primero con construir_exe.bat, abrir este archivo con Inno Setup y pulsar "Compile".
; Resultado: Output\Instalador_ROMO_Inventario.exe

[Setup]
; AppId fijo: permite que una version nueva se instale encima de la anterior sin duplicar el programa
AppId={{6B51C672-8EFF-4D15-A4B1-73E39F3D319E}
AppName=ROMO Inventario
AppVersion=1.0
AppPublisher=ROMO El Rincón del Lubricante
DefaultDirName={autopf}\ROMO Inventario
DefaultGroupName=ROMO Inventario
OutputBaseFilename=Instalador_ROMO_Inventario
SetupIconFile=inventario\assets\icono.ico
UninstallDisplayIcon={app}\ROMO Inventario.exe
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "dist\ROMO Inventario\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autodesktop}\ROMO Inventario"; Filename: "{app}\ROMO Inventario.exe"
Name: "{group}\ROMO Inventario"; Filename: "{app}\ROMO Inventario.exe"

[Run]
Filename: "{app}\ROMO Inventario.exe"; Description: "Abrir ROMO Inventario"; Flags: nowait postinstall skipifsilent
