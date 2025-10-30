@echo off
REM Launcher mejorado: si existe el EXE empaquetado lo ejecuta; si no, ejecuta el script Python.
cd /d "%~dp0"

REM Si existe el ejecutable creado por PyInstaller, úsalo
if exist "%~dp0dist\app_empenos_web.exe" (
	start "Servidor Empeños" "%~dp0dist\app_empenos_web.exe"
) else (
	REM Si existe un entorno virtual .venv, actívalo y ejecuta la app en una nueva ventana
	if exist "%~dp0.venv\Scripts\activate.bat" (
		start "Servidor Empeños" cmd /k "call "%~dp0.venv\Scripts\activate.bat" && python "%~dp0app_empenos_web.py""
	) else (
		start "Servidor Empeños" cmd /k "python "%~dp0app_empenos_web.py""
	)
)

REM Esperar hasta que el servidor responda (máx ~15s) y abrir el navegador automáticamente
powershell -Command "$url='http://127.0.0.1:5000'; for($i=0;$i -lt 15;$i++){ try{Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 2; exit 0} catch {Start-Sleep -Seconds 1}}; exit 1"
if %errorlevel% equ 0 (
	start "" "http://127.0.0.1:5000"
) else (
	echo No se pudo contactar al servidor en 15 segundos. Abre el navegador manualmente en http://127.0.0.1:5000
)
exit
