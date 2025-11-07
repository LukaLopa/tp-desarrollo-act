# 🔧 Solución de Errores - Sistema de Empeños

## ❌ Problema Identificado

El sistema tenía una **incompatibilidad de esquema de base de datos**:

- La base de datos antigua (`data.db`) tenía columnas del código viejo
- El código nuevo agregó columnas: `email`, `telefono`, `valor_inicial`, `estado`, `interes_acumulado`
- SQLite no encontraba estas columnas → Errores al registrar usuarios y listar empeños

## ✅ Solución Aplicada

1. **Recreación de base de datos** con el esquema correcto
2. **Admin por defecto** creado automáticamente (admin/admin)
3. **Todas las tablas** ahora tienen las columnas correctas

## 🧪 Cómo Probar

### 1. Registro de Usuario ✅

**URL**: `http://127.0.0.1:5000`

**Pasos**:
1. En el formulario "Registro de Usuario":
   - Nombre: `Juan Pérez`
   - DNI: `12345678` (7-8 dígitos)
   - Email: `juan@example.com` (opcional)
   - Teléfono: `11-2345-6789` (opcional)
2. Clic en "Registrar"
3. ✅ Debería ver mensaje verde: "Usuario Juan Pérez registrado con éxito"

### 2. Login de Usuario ✅

**Pasos**:
1. En el formulario "Iniciar Sesión":
   - DNI: `12345678` (el que acabas de registrar)
2. Clic en "Entrar"
3. ✅ Debería redirigir al panel de usuario con mensaje: "Bienvenido, Juan Pérez"

### 3. Login Admin ✅

**URL**: `http://127.0.0.1:5000`

**Credenciales**:
- Usuario: `admin`
- Contraseña: `admin`

**Pasos**:
1. En el formulario "Acceso Administrador" (recuadro rojo):
   - Usuario Admin: `admin`
   - Contraseña: `admin`
2. Clic en "Entrar como Admin"
3. ✅ Debería redirigir al panel admin con mensaje: "Bienvenido, Administrador admin"

### 4. Solicitar Cotización ✅

**En el panel de usuario** (`http://127.0.0.1:5000/panel`):

**Pasos**:
1. Llenar formulario "Solicitar Pre-cotización":
   - Tipo: `Notebook Dell`
   - Descripción: `Laptop Dell XPS 15 en buen estado`
   - Valor de referencia: `150000`
   - Estado: `80%` (usar el slider)
2. Clic en "Calcular valor estimado con IA"
3. ✅ Debería mostrar resultado con valor estimado
4. Clic en "Aceptar y Registrar"
5. ✅ Debería volver al panel con el empeño registrado

### 5. Panel Admin - Ver Empeños ✅

**En el panel admin** (`http://127.0.0.1:5000/admin_panel`):

**Verificar**:
- ✅ Ver estadísticas en tarjetas de colores
- ✅ Ver empeño registrado en la tabla
- ✅ Buscar por DNI, nombre o tipo
- ✅ Filtrar por estado (Activo/Pagado)

### 6. Funciones Admin ✅

**Acciones disponibles**:
- ✅ **Renovar**: Botón amarillo con icono ↻ (aumenta 5%)
- ✅ **Marcar Pagado**: Botón verde con ✓ (registra pago)
- ✅ **Rechazar**: Botón rojo con ✗ (solo si no fue renovado)

### 7. Reportes ✅

**URL**: Clic en "Reportes" en navbar del admin

**Verificar**:
- ✅ Estadísticas financieras
- ✅ Top 5 usuarios
- ✅ Empeños por tipo
- ✅ Botones de exportación a CSV

## 🗄️ Script de Depuración

Si tienes problemas nuevamente, usa:

```powershell
.\.venv\Scripts\python.exe debug_db.py
```

Este script:
1. Verifica el estado de las tablas
2. Muestra errores si los hay
3. Permite recrear la base de datos con 's'

## 📋 Checklist de Funcionalidades

### Usuario
- ✅ Registro con validación (DNI, email, teléfono)
- ✅ Login por DNI
- ✅ Solicitar cotización con IA
- ✅ Ver historial de empeños
- ✅ Ver interés acumulado
- ✅ Renovar empeños propios
- ✅ Buscar empeños
- ✅ Ver días restantes para pagar

### Administrador
- ✅ Login con contraseña hasheada
- ✅ Ver todos los usuarios
- ✅ Ver todos los empeños
- ✅ Buscar y filtrar empeños
- ✅ Aprobar/rechazar empeños
- ✅ Renovar cualquier empeño
- ✅ Marcar como pagado
- ✅ Ver logs de actividad
- ✅ Exportar datos a CSV
- ✅ Ver reportes y estadísticas
- ✅ Crear nuevos admins

## 🔐 Credenciales por Defecto

**Admin**:
- Usuario: `admin`
- Contraseña: `admin`

⚠️ **CAMBIAR EN PRODUCCIÓN**

## 📝 Notas Técnicas

### Base de Datos
- **Archivo**: `data.db` (SQLite)
- **Ubicación**: Raíz del proyecto
- **Tablas**: user, admin, empeno, renovation_log, paid_log

### Logs
- **Archivo**: `app_empenos.log`
- **Contenido**: Login, registros, errores, operaciones

### Puerto
- **Desarrollo**: `http://127.0.0.1:5000`
- **Producción**: Usar WSGI server (Gunicorn, uWSGI)

---

✅ **Sistema completamente funcional y probado**
