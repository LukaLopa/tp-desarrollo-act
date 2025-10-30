# Empeños IA — Aplicación web (Flask)

> Proyecto educativo: aplicación web mínima para gestionar empeños con una pequeña parte de IA para estimar valor de empeño.

## Resumen

Esta aplicación es un pequeño sistema de gestión de empeños escrito en Python/Flask. Permite:

- Registrar usuarios (nombre + DNI).
- Iniciar sesión como usuario y ver su panel con sus empeños.
- Pre-cotizar un empeño: enviar datos (valor de referencia y estado) y obtener un valor estimado generado por un modelo de machine learning (RandomForest) integrado.
- Aceptar la cotización para crear un empeño persistido en SQLite.
- Renovar un empeño: reinicia el contador (created_at), aplica un 5% sobre el valor estimado y registra la renovación en un log. El administrador no puede rechazar empeños que ya fueron renovados.
- Interfaz administrativa simple (usuario: `admin`, contraseña: `admin`) para ver todos los empeños y usuarios.
- Empaquetado opcional con PyInstaller; el ejecutable puede arrancar una ventana en la bandeja del sistema usando `pystray` (si está instalado).

La base de datos SQLite se guarda en `data.db` dentro del directorio del proyecto.

## Estructura del proyecto

- `app_empenos_web.py` — archivo principal de la aplicación (rutas, modelos, lógica y servidor).
- `templates/` — plantillas Jinja2 usadas por Flask (`index.html`, `panel.html`, `resultado.html`, `admin.html` si existe).
- `.venv/` — (opcional) entorno virtual local (no debería incluirse en git).
- `build/`, `dist/` — artefactos de PyInstaller (si construiste un EXE).

## Requisitos

- Python 3.10+ recomendado (el repo fue usado con 3.14 en pruebas). 
- Dependencias principales: Flask, pandas, scikit-learn, flask_sqlalchemy, sqlalchemy, pystray (opcional), Pillow (opcional).

Un ejemplo mínimo de `requirements.txt`:

```
Flask
pandas
scikit-learn
flask_sqlalchemy
sqlalchemy
pystray==0.19.5  # opcional (tray)
Pillow               # opcional (tray)
```

## Instalación y ejecución en Windows (PowerShell)

1) Crear y activar un entorno virtual (recomendado):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Instalar dependencias:

```powershell
pip install -r requirements.txt
```

3) Ejecutar la app en modo desarrollo (abrirá el servidor en 127.0.0.1:5000):

```powershell
python .\app_empenos_web.py
```

La aplicación intentará abrir el navegador automáticamente. Si `pystray` está instalado y soportado, la app mostrará un icono en la bandeja con los menús "Abrir navegador" y "Salir".

## Uso (flujo de trabajo)

1. Abrir `http://127.0.0.1:5000`.
2. Registrar un usuario desde la página principal (nombre y DNI).
3. Iniciar sesión con el DNI registrado.
4. En el panel de usuario, completar el formulario de cotización: `valor_ref` y `estado`.
   - Puedes ingresar `estado` como porcentaje (por ejemplo `80`) o como fracción (`0.8`). Internamente se convierte a 0.0–1.0.
5. El modelo devuelve `valor_estimado`. Si estás de acuerdo, presiona `Aceptar` para crear el empeño.
6. Para renovar un empeño (usuario propietario o admin): usar la opción de renovar; esto:
   - Aplica un 5% al `valor_estimado`.
   - Reinicia `created_at` al momento actual (por eso el contador de días restantes se reinicia).
   - Incrementa el contador `renovaciones` y crea una entrada en `RenovationLog`.
7. El admin (usuario `admin` / pass `admin`) puede ver todos los empeños. NOTA: si un empeño ya fue renovado (renovaciones > 0), el admin no podrá rechazarlo.

## Rutas / Endpoints importantes

- GET `/` — página principal (registro / login).
- POST `/registrar` — registrar usuario.
- POST `/login` — login por DNI.
- GET `/panel` — panel del usuario (lista sus empeños).
- POST `/precotizar` — crea una cotización o acepta la cotización y guarda empeño.
- POST `/renovar_empeno` — renovación (usuario propietario o admin).
- POST `/rechazar_empeno` — rechazar un empeño (solo admin, y no si tiene renovaciones).
- GET/POST `/_shutdown` — endpoint interno para pedir al servidor que se apague (usado por el icono de la bandeja).

## Base de datos

- Archivo SQLite: `data.db`.
- Modelos:
  - `User` (id, nombre, dni)
  - `Empeno` (id, user_id, tipo, descripcion, valor_estimado, created_at, term_days, renovaciones)
  - `RenovationLog` (id, empeno_id, by, by_admin, time, old, new)

La base se crea automáticamente al arrancar la aplicación si no existe.

## Packaging (crear EXE con PyInstaller)

Si quieres generar un ejecutable (único archivo) para Windows con PyInstaller, un ejemplo de comando:

```powershell
pip install pyinstaller
pyinstaller --onefile --add-data "templates;templates" --name app_empenos_web app_empenos_web.py
```

Notas:
- PyInstaller puede generar una carpeta `build/` y un único `dist\app_empenos_web.exe`.
- Muchas bibliotecas científicas (numpy, scipy, sklearn) generan advertencias de módulos opcionales en los hooks; normalmente son seguros.
- Si incluyes `pystray` en el EXE y quieres icono en bandeja, asegúrate que `Pillow` esté incluido.

## Limpieza de artefactos y recomendaciones (seguras)

- No incluyas `.venv/` en tu repositorio. Añade esto a `.gitignore`:

```
.venv/
dist/
build/
*.pyc
__pycache__/
data.db
```

- Si quieres liberar espacio en esta carpeta de trabajo local:
  - Mover `.venv` fuera del repo o borrarlo si puedes recrearlo (con `pip install -r requirements.txt`).
  - Borrar `build/` y `dist/` si no necesitas el EXE.

Comandos de ejemplo (PowerShell) para limpiar `build` y `dist`:

```powershell
# Eliminar build y dist (irrecuperable)
Remove-Item -Recurse -Force .\build
Remove-Item -Recurse -Force .\dist
```

Para mover el venv (si quieres conservarlo pero fuera del repo):

```powershell
Rename-Item .venv ..\venv_saved
```

O para borrarlo (si estás seguro):

```powershell
Remove-Item -Recurse -Force .venv
```

## Seguridad y notas finales

- El `app.secret_key` está en claro en el archivo — solo para desarrollo. Si vas a publicar o poner en producción, usa una clave secreta segura y no la incluyas en el repo (usa variables de entorno).
- El manejo de sesión/usuario es simple (variable global `usuario_activo`). Para una app multiusuario real, considera usar `Flask-Login`.
- SQLite es adecuado para prototipos; para producción usa una base más robusta si hace falta concurrencia.

## Problemas comunes y solución rápida

- Si la app no arranca por falta de `pystray` o `Pillow`, instala esas dependencias o deja que el código las omita (tray es opcional).
- Si ves muchos archivos en la carpeta del proyecto, la causa habitual es el entorno virtual `.venv` (contiene los paquetes instalados). Mover/borrar ese venv reduce drásticamente el conteo de archivos.

## Próximos pasos sugeridos

- Reemplazar `usuario_activo` con `Flask-Login` (mejor manejo de sesiones).
- Añadir tests unitarios para los flujos: cotizar, aceptar, renovar y restricción de rechazo por renovación.
- Crear un `requirements.txt` pinneado (con las versiones usadas) para reproducibilidad.

---

Si quieres, puedo:

- Añadir el `requirements.txt` automáticamente con las dependencias actuales.
- Añadir `.gitignore` con las reglas recomendadas.
- Ejecutar la limpieza (mover/borrar `.venv`, `build`, `dist`) — pediré confirmación antes de borrar.

Dime qué prefieres y lo hago.
# Empeños - Lanzador

Este repositorio contiene una versión simple en Flask de un sistema de gestión de empeños con un módulo IA (modelo simulado).

Archivos importantes:
Instrucciones rápidas (Windows):

 
1. Instalar dependencias (recomendado en un entorno virtual):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate; pip install -r requirements.txt
```

2. Ejecutar con el lanzador (elige uno):
- Doble clic en `launch.bat`, o
- Ejecutar en PowerShell: `./launch.ps1` (desde la carpeta del proyecto).

El lanzador abrirá una ventana con el servidor y, tras unos segundos, abrirá la página en tu navegador en `http://127.0.0.1:5000`.

Notas:
- La aplicación usa una clave de sesión de desarrollo (`app.secret_key = 'dev-secret-key'`). No la uses en producción.
- Si quieres ejecutar directamente sin el lanzador: `python app_empenos_web.py`.

Creación de un ejecutable standalone (para distribuir sin que el usuario instale Python)
-----------------------------------------------------------------------

Puedes generar un único ejecutable que incluya Python y tu app usando PyInstaller. Esto lo haces una sola vez en tu máquina de desarrollo y luego distribuyes el `.exe` resultante a usuarios.

1. Instala PyInstaller en tu entorno de desarrollo:

```powershell
pip install pyinstaller
```

2. Ejecuta el script `make_exe.bat` (ya incluido). Este script llama a PyInstaller y empaqueta la app y la carpeta `templates`.

```powershell
.\make_exe.bat
```

3. Tras completarse, encontrarás el ejecutable en `dist\app_empenos_web.exe`. Ese archivo (en la mayoría de los casos) podrá ejecutarse en otra máquina Windows sin instalar Python.

Consideraciones:
- El script `app_empenos_web.py` detecta cuando está "congelado" por PyInstaller y usa las plantillas embebidas. Por eso el EXE resultante encuentra las plantillas correctamente.
- Para crear el EXE necesitas PyInstaller (solo en la máquina que empaqueta). Los usuarios que reciban el EXE no necesitan instalar nada.
- Si quieres que el lanzador o el EXE incluya un entorno virtual completo u otras dependencias nativas, avísame y lo adaptamos.

Si prefieres que el lanzador descargue automáticamente una Python embeddable en tiempo de ejecución (sin instalar), puedo crear un `launch.ps1` alternativo que haga eso; sin embargo, esa opción requiere conexión a Internet la primera vez y puede tardar algo más.

¿Quieres que genere el EXE aquí (no puedo hacerlo en el entorno del repo sin PyInstaller instalado) o prefieres que te guíe paso a paso para crear el EXE en tu máquina?
1. Instalar dependencias (recomendado en un entorno virtual):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate; pip install -r requirements.txt
```

2. Ejecutar con el lanzador (elige uno):
- Doble clic en `launch.bat`, o
- Ejecutar en PowerShell: `.\
elease\launch.ps1` (o `.\\launch.ps1` desde la carpeta del proyecto). 

El lanzador abrirá una ventana con el servidor y, tras unos segundos, abrirá la página en tu navegador en `http://127.0.0.1:5000`.

Notas:
- La aplicación usa una clave de sesión de desarrollo (`app.secret_key = 'dev-secret-key'`). No la uses en producción.
- Si quieres ejecutar directamente sin el lanzador: `python app_empenos_web.py`.

Si quieres que el lanzador espere hasta que el servidor responda (en vez de un tiempo fijo), puedo actualizar el script para hacer una comprobación HTTP antes de abrir el navegador.
#   t p - d e s a r r o l l o  
 