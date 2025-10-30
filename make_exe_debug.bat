@echo off
REM make_exe_debug.bat
REM Script para reconstruir el ejecutable con PyInstaller (modo DEBUG / con consola)
REM Ubica este archivo en la raíz del proyecto (junto a app_empenos_web.py).

:: Limpiar builds previos
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist app_empenos_web.spec del /q app_empenos_web.spec

:: Usar python del venv si existe, sino usar python del sistema
set PYTHON_CMD=python
if exist .venv\Scripts\python.exe (
    set PYTHON_CMD=.venv\Scripts\python.exe
    echo Usando Python de .venv -> %PYTHON_CMD%
) else (
    echo No se detecto un virtualenv en .venv; se usara el Python del sistema.
)

:: Asegurarse pip y dependencias
%PYTHON_CMD% -m pip install --upgrade pip
if exist requirements.txt (
    %PYTHON_CMD% -m pip install -r requirements.txt
) else (
    echo requirements.txt no encontrado; instala manualmente Flask, scikit-learn, pandas, flask_sqlalchemy, pyinstaller, pystray, Pillow, etc.
)

:: Asegurarse de que PyInstaller esté instalado
%PYTHON_CMD% -m pip install pyinstaller

:: Ejecutar PyInstaller en modo debug (con consola visible)
:: Nota: el separador en --add-data es ";" en Windows: "origen;dest"
%PYTHON_CMD% -m PyInstaller --clean --onefile --console --add-data "templates;templates" --hidden-import=pkg_resources.py2_warn --hidden-import=sklearn --hidden-import=pandas --hidden-import=joblib --hidden-import=numpy --hidden-import=pystray --hidden-import=pystray._win32 --hidden-import=PIL --hidden-import=PIL.Image --collect-all sklearn app_empenos_web.py > build_log_debug.txt 2>&1

echo Build (debug) finalizado o fallado. Revisa build_log_debug.txt para ver la salida completa.
echo Si la build falló, pega aqui el contenido de build_log_debug.txt para que lo analice.
pause
