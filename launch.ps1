# Launcher PowerShell mejorado:
# - Ejecuta el EXE si existe
# - Si no, activa .venv (si está) y ejecuta la app en una nueva ventana de PowerShell
# - Espera a que el servidor responda antes de abrir el navegador
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

# Si hay EXE empaquetado, ejecútalo
if (Test-Path "$scriptDir\dist\app_empenos_web.exe") {
	Start-Process -FilePath "$scriptDir\dist\app_empenos_web.exe"
} else {
	# Preparar comando para ejecutar la app
	if (Test-Path "$scriptDir\.venv\Scripts\Activate.ps1") {
		$cmd = "& '$scriptDir\\.venv\\Scripts\\Activate.ps1'; python '$scriptDir\\app_empenos_web.py'"
	} else {
		$cmd = "python '$scriptDir\\app_empenos_web.py'"
	}
	# Abrir nueva ventana de PowerShell que ejecute el comando y la deje abierta para ver logs
	Start-Process -FilePath powershell -ArgumentList '-NoExit', '-Command', $cmd
}

# Esperar a que el servidor responda (hasta 15 segundos) y abrir el navegador
$url = 'http://127.0.0.1:5000'
for ($i = 0; $i -lt 15; $i++) {
	try {
		Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 2 | Out-Null
		Start-Process $url
		break
	} catch {
		Start-Sleep -Seconds 1
	}
}
