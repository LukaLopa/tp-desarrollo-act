# Empeños IA — Aplicación web (Flask)

Sistema de gestión de empeños con modelo IA para estimar valores.

## Requisitos

- **Python 3.10+**
- **Dependencias**: Ver 'requirements.txt'

## Instalación rápida

1. Crear entorno virtual:
   python -m venv .venv
   .\\.venv\Scripts\Activate.ps1

2. Instalar dependencias:
   pip install -r requirements.txt

3. Ejecutar la aplicación:
   python app_empenos_web.py

La app abrirá automáticamente en http://127.0.0.1:5000

## Funcionamiento

**Panel de Usuario:**
- Registrarse con nombre y DNI
- Iniciar sesión por DNI
- Cotizar empeños (ingresando valor de referencia y estado del artículo)
- Ver historial de empeños
- Renovar empeños (aplica 5% al valor)

**Agendamiento de citas (novedad):**
- Después de aceptar y registrar una pre-cotización, el sistema redirige al usuario a un formulario para agendar una cita asociada al empeño registrado.
- Solo se permiten fechas posteriores al día actual (validación server-side y client-side). La hora debe estar en formato HH:MM.
- El sistema evita dobles reservas: no se puede crear una nueva cita si ya existe otra 'pendiente' o 'confirmada' en la misma fecha y hora.
- El usuario puede ver sus citas en `Mi Panel` (sección "Mis Citas") con fecha, hora, estado y referencia al número de pre-cotización si aplica.

**Panel Administrativo (cambios relativos a citas):**
- Los administradores ven las citas recientes en el panel de administración.
- El admin puede confirmar o rechazar una cita desde el panel (`/admin_panel` → sección Citas). Al confirmar/rechazar se actualiza el estado de la cita.

**Panel Administrativo:**
- Usuario: admin | Contraseña: admin
- Ver todos los empeños y usuarios
- Aceptar/rechazar empeños
- Marcar empeños como pagados
- Ver reportes y estadísticas

## Estructura

- app_empenos_web.py — Aplicación principal
- templates/ — Plantillas HTML
   - `agendar_cita.html` — formulario para agendar una cita asociada a un empeño
   - `panel.html` — ahora incluye sección "Mis Citas" para que el usuario vea sus citas
- requirements.txt — Dependencias Python
- launch.bat / launch.ps1 — Scripts de inicio
- instance/ — Base de datos SQLite (creada automáticamente)

## Notas

- Base de datos: data.db se crea automáticamente en instance/
- Abre navegador automáticamente al iniciar
- Si está instalado pystray, la app se minimiza a bandeja del sistema
 - Rutas relacionadas con citas:
    - `POST /agendar_cita` — crea una cita (login requerido). Valida fecha/hora y previene doble-reserva.
    - `GET /agendar_cita/<empeno_id>` — formulario para agendar cita asociada a un empeño.
    - `POST /admin/cita/accion` — endpoint para que el admin confirme o rechace una cita.

Si quieres que añada cancelación de citas por parte del usuario, notificaciones por email al confirmar/rechazar, o una lógica de slots más avanzada (p.ej. evitar solapes por intervalo), puedo implementarlo como siguiente mejora.
