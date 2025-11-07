# 💎 Sistema de Gestión de Empeños - Versión Mejorada

Sistema completo de gestión de empeños con inteligencia artificial, diseño moderno y funcionalidades avanzadas.

## 🚀 Mejoras Implementadas

### 🔒 Seguridad
- ✅ **Hash de contraseñas** con Werkzeug para administradores
- ✅ **Validación de inputs** (DNI, email, teléfono, datos numéricos)
- ✅ **Sanitización de datos** para prevenir inyecciones
- ✅ **Sesiones seguras** con timeout de 2 horas
- ✅ **Decoradores de autenticación** (@login_required, @admin_required)
- ✅ **Logging completo** de operaciones críticas
- ✅ **Manejo de errores** mejorado (404, 500)

### 🏗️ Arquitectura
- ✅ **Modelos extendidos**:
  - `User`: email, teléfono, fecha de creación
  - `Admin`: autenticación con contraseña hasheada
  - `Empeno`: valor inicial, interés acumulado, estado
  - `PaidLog`: monto e interés pagado
- ✅ **Funciones de utilidad** (validación, sanitización, cálculos)
- ✅ **Sistema de mensajes flash** para feedback al usuario
- ✅ **Configuración desde variables de entorno**

### 💰 Funcionalidad de Negocio
- ✅ **Sistema de intereses**:
  - 5% por renovación
  - 0.1% interés diario acumulado
  - Cálculo automático del total a pagar
- ✅ **Estados de empeño**: activo, pagado, vencido
- ✅ **Búsqueda avanzada** en panel de usuario y admin
- ✅ **Filtros por estado** en panel admin
- ✅ **Exportación a CSV** (usuarios, empeños, pagos)
- ✅ **Sistema de reportes** con estadísticas detalladas

### 🎨 Interfaz de Usuario
- ✅ **Bootstrap 5** con diseño responsive
- ✅ **Iconos Bootstrap Icons**
- ✅ **Diseño moderno** con gradientes y animaciones
- ✅ **Cards interactivas** con hover effects
- ✅ **Mensajes flash** con auto-cierre
- ✅ **Confirmaciones JavaScript** para acciones críticas
- ✅ **Tabs organizadas** en panel admin
- ✅ **Progress bars** en reportes
- ✅ **Badges de estado** con colores semánticos

### 📊 Reportes y Estadísticas
- ✅ **Dashboard de métricas**:
  - Total de empeños, activos, pagados
  - Capital activo, total recuperado
  - Intereses generados
- ✅ **Top 5 usuarios** con más empeños
- ✅ **Distribución por tipo** de objeto
- ✅ **Gráficos visuales** con progress bars

### 🔧 Funcionalidades Técnicas
- ✅ **Admin por defecto** (admin/admin) creado automáticamente
- ✅ **Creación de nuevos admins** desde el panel
- ✅ **API REST endpoint** (/api/stats) para integraciones futuras
- ✅ **Log de actividad** guardado en archivo
- ✅ **Manejo de pystray opcional** (bandeja del sistema)

## 📦 Instalación y Ejecución

### Requisitos
- Python 3.8+
- Entorno virtual (venv)

### Pasos

1. **Crear entorno virtual e instalar dependencias**:
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

2. **Ejecutar la aplicación**:
```powershell
.\.venv\Scripts\python.exe .\app_empenos_web.py
```

3. **Acceder al sistema**:
   - Navegador se abre automáticamente en `http://127.0.0.1:5000`
   - Admin por defecto: `admin` / `admin`

## 📖 Uso del Sistema

### Para Usuarios

1. **Registro**:
   - Nombre completo, DNI (7-8 dígitos)
   - Email y teléfono opcionales

2. **Solicitar cotización**:
   - Tipo de objeto (Joya, Electrónico, etc.)
   - Descripción detallada
   - Valor de referencia
   - Estado del objeto (0-100%)
   - IA calcula el valor estimado

3. **Gestionar empeños**:
   - Ver historial completo
   - Días restantes para pagar
   - Interés acumulado
   - Renovar empeños (5% interés)
   - Buscar por tipo o descripción

### Para Administradores

1. **Login admin**:
   - Usuario: `admin`
   - Contraseña: `admin` (cambiar en producción)

2. **Panel de administración**:
   - Ver todos los empeños y usuarios
   - Buscar y filtrar por estado
   - Aprobar/rechazar empeños
   - Renovar empeños de usuarios
   - Marcar como pagado
   - Ver logs de actividad

3. **Reportes**:
   - Estadísticas generales
   - Métricas financieras
   - Top usuarios
   - Distribución por tipo

4. **Exportación**:
   - Exportar usuarios a CSV
   - Exportar empeños a CSV
   - Exportar pagos a CSV

5. **Gestión de admins**:
   - Crear nuevos administradores
   - Contraseñas hasheadas automáticamente

## 🔑 Credenciales por Defecto

**Administrador**:
- Usuario: `admin`
- Contraseña: `admin`

⚠️ **IMPORTANTE**: Cambiar la contraseña del admin en producción.

## 🗃️ Base de Datos

SQLite con las siguientes tablas:
- `user`: Usuarios del sistema
- `admin`: Administradores con contraseñas hasheadas
- `empeno`: Empeños registrados
- `renovation_log`: Historial de renovaciones
- `paid_log`: Historial de pagos

## 📂 Estructura de Archivos

```
tp-desarrolloluka/
├── app_empenos_web.py          # Aplicación principal mejorada
├── requirements.txt            # Dependencias
├── data.db                     # Base de datos SQLite
├── app_empenos.log            # Archivo de logs
├── templates/
│   ├── base.html              # Template base con Bootstrap
│   ├── index.html             # Página de inicio
│   ├── panel.html             # Panel de usuario
│   ├── admin.html             # Panel de administración
│   ├── resultado.html         # Resultado de cotización
│   └── reportes.html          # Reportes y estadísticas
└── .venv/                     # Entorno virtual
```

## 🎯 Características Destacadas

### Sistema de Intereses Inteligente
- **Interés por renovación**: 5% del valor actual
- **Interés diario**: 0.1% sobre el valor inicial
- **Cálculo automático**: Total a pagar = Valor + Interés acumulado

### Búsqueda y Filtros
- Búsqueda por tipo, descripción, DNI o nombre
- Filtros por estado (activo, pagado, vencido)
- Resultados en tiempo real

### Exportación de Datos
- Formato CSV compatible con Excel
- Incluye todos los campos relevantes
- Timestamp en nombre de archivo

### UI/UX Moderna
- Diseño responsive (móvil, tablet, desktop)
- Animaciones suaves
- Feedback visual inmediato
- Confirmaciones para acciones críticas

## 🔐 Seguridad

- Contraseñas hasheadas con SHA-256
- Validación de inputs en servidor
- Sanitización contra inyecciones
- Sesiones con timeout
- Logging de operaciones críticas
- Mensajes de error genéricos (no exponen información sensible)

## 📊 Logging

Archivo `app_empenos.log` registra:
- Login exitosos y fallidos
- Operaciones CRUD
- Errores y excepciones
- Exportaciones de datos

## 🚀 Próximas Mejoras (Opcionales)

- [ ] Autenticación de dos factores (2FA)
- [ ] Notificaciones por email/SMS
- [ ] Dashboard con gráficos interactivos (Chart.js)
- [ ] Respaldo automático de base de datos
- [ ] Multi-tenancy (múltiples casas de empeño)
- [ ] App móvil (React Native / Flutter)
- [ ] Integración con WhatsApp Business

## 📝 Notas de Desarrollo

- **Framework**: Flask 3.1+
- **ORM**: SQLAlchemy
- **ML**: Scikit-learn (Random Forest)
- **Frontend**: Bootstrap 5 + Bootstrap Icons
- **Base de datos**: SQLite (fácil migración a PostgreSQL/MySQL)

## 🤝 Contribuciones

Sistema desarrollado con las mejores prácticas de:
- Clean Code
- SOLID principles
- Security first
- User experience

---

**Desarrollado con ❤️ para modernizar la gestión de empeños**

🔒 Seguro | 🚀 Rápido | 💎 Profesional
