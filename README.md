# Empeños IA — Aplicación web (Flask)# Empeños IA — Aplicación web (Flask)



Sistema de gestión de empeños con modelo IA para estimar valores.Sistema de gestión de empeños con modelo IA para estimar valores.



## Requisitos## Requisitos



- **Python 3.10+**- **Python 3.10+**

- **Dependencias**: Ver `requirements.txt`- **Dependencias**: Ver 

equirements.txt

## Instalación rápida

## Instalación rápida

1. Crear entorno virtual:

```powershell1. Crear entorno virtual:

python -m venv .venv``powershell

.\.venv\Scripts\Activate.ps1python -m venv .venv

```.\.venv\Scripts\Activate.ps1

``

2. Instalar dependencias:

```powershell2. Instalar dependencias:

pip install -r requirements.txt``powershell

```pip install -r requirements.txt

``

3. Ejecutar la aplicación:

```powershell3. Ejecutar la aplicación:

python app_empenos_web.py``powershell

```python app_empenos_web.py

``

La app abrirá automáticamente en `http://127.0.0.1:5000`.

La app abrirá automáticamente en http://127.0.0.1:5000.

## Funcionamiento

## Funcionamiento

**Panel de Usuario:**

- Registrarse con nombre y DNI**Panel de Usuario:**

- Iniciar sesión por DNI- Registrarse con nombre y DNI

- Cotizar empeños (ingresando valor de referencia y estado del artículo)- Iniciar sesión por DNI

- Ver historial de empeños- Cotizar empeños (ingresando valor de referencia y estado del artículo)

- Renovar empeños (aplica 5% al valor)- Ver historial de empeños

- Renovar empeños (aplica 5% al valor)

**Panel Administrativo:**

- Usuario: `admin`**Panel Administrativo:**

- Contraseña: `admin`- Usuario: dmin

- Ver todos los empeños y usuarios- Contraseña: dmin

- Aceptar/rechazar empeños- Ver todos los empeños y usuarios

- Marcar empeños como pagados- Aceptar/rechazar empeños

- Ver reportes y estadísticas- Marcar empeños como pagados

- Ver reportes y estadísticas

## Estructura

## Estructura

- `app_empenos_web.py` — Aplicación principal

- `templates/` — Plantillas HTML (Flask)- pp_empenos_web.py — Aplicación principal

- `requirements.txt` — Dependencias Python- 	emplates/ — Plantillas HTML (Flask)

- `launch.bat` / `launch.ps1` — Scripts de inicio- 

- `instance/` — Base de datos SQLite (se crea automáticamente)equirements.txt — Dependencias Python

- launch.bat / launch.ps1 — Scripts de inicio

## Notas- instance/ — Base de datos SQLite (se crea automáticamente)



- La base de datos SQLite (`data.db`) se crea automáticamente en `instance/`## Notas

- Abre navegador automáticamente al ejecutar

- Si está instalado `pystray`, la app se minimiza a bandeja del sistema- La base de datos SQLite (data.db) se crea automáticamente en instance/

- Abre navegador automáticamente al ejecutar
- Si está instalado pystray, la app se minimiza a bandeja del sistema
