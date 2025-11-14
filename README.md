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

**Panel Administrativo:**
- Usuario: admin | Contraseña: admin
- Ver todos los empeños y usuarios
- Aceptar/rechazar empeños
- Marcar empeños como pagados
- Ver reportes y estadísticas

## Estructura

- app_empenos_web.py — Aplicación principal
- templates/ — Plantillas HTML
- requirements.txt — Dependencias Python
- launch.bat / launch.ps1 — Scripts de inicio
- instance/ — Base de datos SQLite (creada automáticamente)

## Notas

- Base de datos: data.db se crea automáticamente en instance/
- Abre navegador automáticamente al iniciar
- Si está instalado pystray, la app se minimiza a bandeja del sistema
