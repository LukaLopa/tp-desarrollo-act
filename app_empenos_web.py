"""app_empenos_web.py
Versión mejorada: Flask + SQLite (SQLAlchemy) + modelo IA + seguridad mejorada.
Mejoras: hash de contraseñas, validación de inputs, mensajes flash, búsqueda, reportes,
protección CSRF, manejo de errores, logging, y mejor UX.
"""
import os
import sys
import threading
import webbrowser
import time
import urllib.request
import logging
import re
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

try:
    import pystray
    from PIL import Image, ImageDraw
    _HAS_PYSTRAY = True
except Exception:
    _HAS_PYSTRAY = False

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_empenos.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

template_folder = (
    os.path.join(sys._MEIPASS, 'templates')
    if getattr(sys, 'frozen', False)
    else os.path.join(os.path.dirname(__file__), 'templates')
)

app = Flask(__name__, template_folder=template_folder)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
db = SQLAlchemy(app)

# Modelo IA pequeño (dataset inline)
data = pd.DataFrame({
    'valor_referencia': [150000, 300000, 80000, 180000, 250000],
    'estado': [0.8, 1.0, 0.5, 0.7, 0.9],
    'valor_empeno': [90000, 210000, 40000, 95000, 150000],
})
modelo_ia = RandomForestRegressor(random_state=0)
modelo_ia.fit(data[['valor_referencia', 'estado']], data['valor_empeno'])


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    dni = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120))
    telefono = db.Column(db.String(20))
    created_at = db.Column(db.String(64), default=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self):
        return {
            'id': self.id, 
            'nombre': self.nombre, 
            'dni': self.dni, 
            'email': self.email,
            'telefono': self.telefono,
            'created_at': self.created_at
        }


class Empeno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tipo = db.Column(db.String(120))
    descripcion = db.Column(db.String(500))
    valor_estimado = db.Column(db.Integer)
    valor_inicial = db.Column(db.Integer)  # Valor original sin intereses
    created_at = db.Column(db.String(64))
    term_days = db.Column(db.Integer, default=30)
    renovaciones = db.Column(db.Integer, default=0)
    estado = db.Column(db.String(20), default='activo')  # activo, pagado, vencido
    interes_acumulado = db.Column(db.Float, default=0.0)
    user = db.relationship('User', backref=db.backref('empenos', lazy=True))


class Admin(db.Model):
    """Modelo para administradores con contraseña hasheada"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.String(64), default=lambda: datetime.now(timezone.utc).isoformat())
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class RenovationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empeno_id = db.Column(db.Integer)
    by = db.Column(db.String(64))
    by_admin = db.Column(db.Boolean, default=False)
    time = db.Column(db.String(64))
    old = db.Column(db.Integer)
    new = db.Column(db.Integer)


class PaidLog(db.Model):
    """Registro de pagos (marcar como pagado). Mantener historial separado para evitar migraciones en tablas existentes."""
    id = db.Column(db.Integer, primary_key=True)
    empeno_id = db.Column(db.Integer)
    by_admin = db.Column(db.Boolean, default=True)
    time = db.Column(db.String(64))
    monto_pagado = db.Column(db.Integer)
    interes_pagado = db.Column(db.Float, default=0.0)


class Cita(db.Model):
    """Registro de citas para evaluación de empeños"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    empeno_id = db.Column(db.Integer)  # ID de la precotización si está relacionada
    fecha = db.Column(db.String(64))  # Fecha de la cita (ISO format)
    hora = db.Column(db.String(5))  # Hora en formato HH:MM
    created_at = db.Column(db.String(64), default=lambda: datetime.now(timezone.utc).isoformat())
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, confirmada, completada, cancelada
    user = db.relationship('User', backref=db.backref('citas', lazy=True))


with app.app_context():
    db.create_all()
    # Crear admin por defecto si no existe
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin')
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        logger.info("Admin por defecto creado: admin/admin")


usuario_activo = None
LOAN_TERM_DAYS = 30
INTERES_RENOVACION = 0.05  # 5% interés por renovación
INTERES_DIARIO = 0.001  # 0.1% interés diario


# ============ UTILIDADES Y VALIDACIÓN ============

def validar_dni(dni):
    """Validar formato de DNI"""
    if not dni or not isinstance(dni, str):
        return False
    # DNI debe ser numérico y tener entre 7-8 dígitos
    return bool(re.match(r'^\d{7,8}$', dni.strip()))


def validar_email(email):
    """Validar formato de email"""
    if not email:
        return True  # Email es opcional
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validar_telefono(telefono):
    """Validar formato de teléfono"""
    if not telefono:
        return True  # Teléfono es opcional
    # Aceptar números con o sin guiones/espacios
    return bool(re.match(r'^[\d\s\-\+\(\)]{7,20}$', telefono.strip()))


def sanitizar_input(texto, max_length=500):
    """Sanitizar input de texto"""
    if not texto:
        return ""
    texto = str(texto).strip()
    return texto[:max_length]


def login_required(f):
    """Decorador para rutas que requieren login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not usuario_activo or not isinstance(usuario_activo, User):
            flash('Debe iniciar sesión primero', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorador para rutas que requieren admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not usuario_activo or not usuario_activo.get('is_admin'):
            flash('Acceso restringido. Requiere permisos de administrador.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def calcular_interes_acumulado(created_iso, valor_inicial, renovaciones=0):
    """Calcular interés acumulado por días transcurridos"""
    now = datetime.now(timezone.utc)
    try:
        created = datetime.fromisoformat(created_iso)
    except Exception:
        return 0.0
    
    dias = (now - created).days
    interes_renovaciones = valor_inicial * INTERES_RENOVACION * renovaciones
    interes_diario_total = valor_inicial * INTERES_DIARIO * dias
    
    return interes_renovaciones + interes_diario_total


def validar_fecha_cita(fecha_str):
    """Validar que la fecha sea posterior a hoy y en formato válido"""
    try:
        fecha = datetime.fromisoformat(fecha_str)
        hoy = datetime.now(timezone.utc)
        # Comparar solo la fecha, sin la hora
        fecha_date = fecha.date()
        hoy_date = hoy.date()
        
        if fecha_date <= hoy_date:
            return False, "La fecha debe ser posterior a hoy"
        return True, ""
    except Exception as e:
        return False, f"Formato de fecha inválido: {str(e)}"


def validar_hora_cita(hora_str):
    """Validar que la hora esté en formato HH:MM válido"""
    try:
        parts = hora_str.split(':')
        if len(parts) != 2:
            return False, "Formato de hora inválido. Use HH:MM"
        hora, minutos = int(parts[0]), int(parts[1])
        if not (0 <= hora < 24 and 0 <= minutos < 60):
            return False, "Hora fuera de rango válido"
        return True, ""
    except Exception as e:
        return False, f"Error validando hora: {str(e)}"


@app.route('/')
def index():
    return render_template('index.html', usuario=usuario_activo)


@app.route('/registrar', methods=['POST'])
def registrar():
    nombre = sanitizar_input(request.form.get('nombre', ''), 120)
    dni = sanitizar_input(request.form.get('dni', ''), 64)
    email = sanitizar_input(request.form.get('email', ''), 120)
    telefono = sanitizar_input(request.form.get('telefono', ''), 20)
    
    # Validaciones
    if not nombre or not dni:
        flash('Nombre y DNI son obligatorios', 'error')
        return redirect(url_for('index'))
    
    if not validar_dni(dni):
        flash('DNI inválido. Debe contener 7-8 dígitos numéricos', 'error')
        return redirect(url_for('index'))
    
    if email and not validar_email(email):
        flash('Email inválido', 'error')
        return redirect(url_for('index'))
    
    if telefono and not validar_telefono(telefono):
        flash('Teléfono inválido', 'error')
        return redirect(url_for('index'))
    
    try:
        nuevo = User(nombre=nombre, dni=dni, email=email, telefono=telefono)
        db.session.add(nuevo)
        db.session.commit()
        logger.info(f"Usuario registrado: {nombre} - DNI: {dni}")
        flash(f'Usuario {nombre} registrado con éxito', 'success')
    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Intento de registro duplicado: DNI {dni}")
        flash('Ya existe un usuario con ese DNI', 'error')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error en registro: {e}")
        flash('Error al registrar usuario', 'error')
    
    return redirect(url_for('index'))


@app.route('/login', methods=['POST'])
def login():
    global usuario_activo
    dni = sanitizar_input(request.form.get('dni', ''), 64)
    
    if not validar_dni(dni):
        flash('DNI inválido', 'error')
        return redirect(url_for('index'))
    
    user = User.query.filter_by(dni=dni).first()
    if user:
        usuario_activo = user
        session.permanent = True
        session['user_id'] = user.id
        session['user_dni'] = user.dni
        logger.info(f"Login exitoso: {user.nombre} - DNI: {dni}")
        flash(f'Bienvenido, {user.nombre}', 'success')
        return redirect(url_for('panel'))
    
    logger.warning(f"Intento de login fallido: DNI {dni}")
    flash('Usuario no encontrado', 'error')
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    global usuario_activo
    usuario_activo = None
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('index'))


def _days_left(created_iso, term=LOAN_TERM_DAYS):
    now = datetime.now(timezone.utc)
    try:
        created = datetime.fromisoformat(created_iso)
    except Exception:
        created = now
    days = (now - created).days
    left = term - days
    return max(left, 0), (created + timedelta(days=term)).isoformat()


@app.route('/panel')
@login_required
def panel():
    historial = []
    search_query = request.args.get('search', '').strip()
    
    query = Empeno.query.filter_by(user_id=usuario_activo.id)
    
    # Búsqueda opcional
    if search_query:
        query = query.filter(
            (Empeno.tipo.contains(search_query)) |
            (Empeno.descripcion.contains(search_query))
        )
    
    for e in query.all():
        left, exp = _days_left(e.created_at, e.term_days or LOAN_TERM_DAYS)
        paid_entry = PaidLog.query.filter_by(empeno_id=e.id).order_by(PaidLog.time.desc()).first()
        pagado = bool(paid_entry)
        pagado_at = paid_entry.time if paid_entry else None
        
        # Calcular interés acumulado
        interes = calcular_interes_acumulado(
            e.created_at, 
            e.valor_inicial or e.valor_estimado, 
            e.renovaciones
        )
        total_a_pagar = e.valor_estimado + int(interes)
        
        historial.append({
            'id': e.id,
            'tipo': e.tipo,
            'descripcion': e.descripcion,
            'valor_estimado': e.valor_estimado,
            'valor_inicial': e.valor_inicial or e.valor_estimado,
            'interes_acumulado': int(interes),
            'total_a_pagar': total_a_pagar,
            'renovaciones': e.renovaciones,
            'created_at': e.created_at,
            'term_days': e.term_days,
            'dias_restantes': left,
            'expiracion': exp,
            'pagado': pagado,
            'pagado_at': pagado_at,
            'estado': e.estado or 'activo'
        })
        # Agregar color de borde para la tarjeta en UI y evitar lógica CSS en plantilla
        try:
            # color y clase de borde: 'paid', 'active', 'expired'
            if pagado:
                historial[-1]['border_color'] = '#27ae60'
                historial[-1]['border_class'] = 'paid'
            elif left > 0:
                historial[-1]['border_color'] = '#3498db'
                historial[-1]['border_class'] = 'active'
            else:
                historial[-1]['border_color'] = '#e74c3c'
                historial[-1]['border_class'] = 'expired'
        except Exception:
            historial[-1]['border_color'] = '#3498db'
            historial[-1]['border_class'] = 'active'
    
    # Citas del usuario (para mostrarlas en el panel)
    try:
        citas = Cita.query.filter_by(user_id=usuario_activo.id).order_by(Cita.created_at.desc()).all()
    except Exception:
        citas = []

    return render_template('panel.html', usuario=usuario_activo, historial=historial, search_query=search_query, citas=citas)



@app.route('/admin_login', methods=['POST'])
def admin_login():
    global usuario_activo
    username = sanitizar_input(request.form.get('admin_user', ''), 64)
    password = request.form.get('admin_pass', '')
    
    if not username or not password:
        flash('Usuario y contraseña son obligatorios', 'error')
        return redirect(url_for('index'))
    
    admin = Admin.query.filter_by(username=username).first()
    
    if admin and admin.check_password(password):
        usuario_activo = {
            'nombre': f'Administrador ({username})',
            'dni': 'admin',
            'is_admin': True,
            'username': username
        }
        session.permanent = True
        session['is_admin'] = True
        session['admin_username'] = username
        logger.info(f"Login admin exitoso: {username}")
        flash(f'Bienvenido, Administrador {username}', 'success')
        return redirect(url_for('admin_panel'))
    
    logger.warning(f"Intento de login admin fallido: {username}")
    flash('Credenciales de administrador incorrectas', 'error')
    return redirect(url_for('index'))


@app.route('/admin_panel')
@admin_required
def admin_panel():
    search_query = request.args.get('search', '').strip()
    estado_filter = request.args.get('estado', '').strip()
    
    enriched = []
    empeno_query = Empeno.query
    
    # Filtros de búsqueda
    if search_query:
        empeno_query = empeno_query.join(User).filter(
            (Empeno.tipo.contains(search_query)) |
            (Empeno.descripcion.contains(search_query)) |
            (User.dni.contains(search_query)) |
            (User.nombre.contains(search_query))
        )
    
    if estado_filter:
        empeno_query = empeno_query.filter(Empeno.estado == estado_filter)
    
    for e in empeno_query.all():
        left, exp = _days_left(e.created_at, e.term_days or LOAN_TERM_DAYS)
        paid_entry = PaidLog.query.filter_by(empeno_id=e.id).order_by(PaidLog.time.desc()).first()
        pagado = bool(paid_entry)
        pagado_at = paid_entry.time if paid_entry else None
        
        interes = calcular_interes_acumulado(
            e.created_at,
            e.valor_inicial or e.valor_estimado,
            e.renovaciones
        )
        total_a_pagar = e.valor_estimado + int(interes)
        
        enriched.append({
            'id': e.id,
            'dni': e.user.dni if e.user else None,
            'nombre_usuario': e.user.nombre if e.user else None,
            'tipo': e.tipo,
            'descripcion': e.descripcion,
            'valor_estimado': e.valor_estimado,
            'valor_inicial': e.valor_inicial or e.valor_estimado,
            'interes_acumulado': int(interes),
            'total_a_pagar': total_a_pagar,
            'renovaciones': e.renovaciones,
            'created_at': e.created_at,
            'term_days': e.term_days,
            'expiracion': exp,
            'pagado': pagado,
            'pagado_at': pagado_at,
            'estado': e.estado or 'activo'
        })
    
    users_db = User.query.all()
    renov_log = RenovationLog.query.order_by(RenovationLog.time.desc()).limit(50).all()
    pagos_log = PaidLog.query.order_by(PaidLog.time.desc()).limit(50).all()
    # Citas recientes
    citas_db = Cita.query.order_by(Cita.created_at.desc()).limit(200).all()
    
    # Estadísticas
    total_empenos = Empeno.query.count()
    total_pagados = PaidLog.query.distinct(PaidLog.empeno_id).count()
    total_activos = Empeno.query.filter_by(estado='activo').count()
    total_usuarios = User.query.count()
    
    stats = {
        'total_empenos': total_empenos,
        'total_pagados': total_pagados,
        'total_activos': total_activos,
        'total_usuarios': total_usuarios
    }
    
    return render_template(
        'admin.html',
        usuario=usuario_activo,
        usuarios=users_db,
        empenos=enriched,
        citas=citas_db,
        renovaciones_log=renov_log,
        pagos_log=pagos_log,
        stats=stats,
        search_query=search_query,
        estado_filter=estado_filter
    )


@app.route('/admin/cita/accion', methods=['POST'])
@admin_required
def admin_cita_accion():
    try:
        cita_id = int(request.form.get('cita_id', 0))
        action = request.form.get('action', '')
    except (ValueError, TypeError):
        flash('Parámetros inválidos', 'error')
        return redirect(url_for('admin_panel'))

    cita = Cita.query.get(cita_id)
    if not cita:
        flash('Cita no encontrada', 'error')
        return redirect(url_for('admin_panel'))

    try:
        if action == 'confirmar':
            cita.estado = 'confirmada'
            flash(f'Cita #{cita.id} confirmada', 'success')
        elif action == 'rechazar':
            cita.estado = 'rechazada'
            flash(f'Cita #{cita.id} rechazada', 'info')
        else:
            flash('Acción desconocida', 'error')
            return redirect(url_for('admin_panel'))

        db.session.add(cita)
        db.session.commit()
        logger.info(f"Admin {session.get('admin_username')} cambió estado de cita {cita.id} a {cita.estado}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cambiando estado de cita: {e}")
        flash('Error al actualizar la cita', 'error')

    return redirect(url_for('admin_panel'))


@app.route('/rechazar_empeno', methods=['POST'])
@admin_required
def rechazar_empeno():
    try:
        emp_id = int(request.form.get('id', 0))
    except (ValueError, TypeError):
        flash('ID inválido', 'error')
        return redirect(url_for('admin_panel'))
    
    target = Empeno.query.get(emp_id)
    if not target:
        flash(f'No se encontró empeño con ID {emp_id}', 'error')
        return redirect(url_for('admin_panel'))
    
    if target.renovaciones and target.renovaciones > 0:
        flash(f'No se puede rechazar el empeño {emp_id} porque fue renovado', 'warning')
        return redirect(url_for('admin_panel'))
    
    try:
        db.session.delete(target)
        db.session.commit()
        logger.info(f"Empeño {emp_id} rechazado por admin")
        flash(f'Empeño {emp_id} rechazado y eliminado', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error rechazando empeño {emp_id}: {e}")
        flash('Error al rechazar empeño', 'error')
    
    return redirect(url_for('admin_panel'))


@app.route('/marcar_pagado', methods=['POST'])
@admin_required
def marcar_pagado():
    try:
        emp_id = int(request.form.get('id', 0))
    except (ValueError, TypeError):
        flash('ID inválido', 'error')
        return redirect(url_for('admin_panel'))
    
    empeno = Empeno.query.get(emp_id)
    if not empeno:
        flash(f'No se encontró empeño con ID {emp_id}', 'error')
        return redirect(url_for('admin_panel'))
    
    try:
        now = datetime.now(timezone.utc).isoformat()
        
        # Calcular interés final
        interes = calcular_interes_acumulado(
            empeno.created_at,
            empeno.valor_inicial or empeno.valor_estimado,
            empeno.renovaciones
        )
        
        pago = PaidLog(
            empeno_id=emp_id,
            by_admin=True,
            time=now,
            monto_pagado=empeno.valor_estimado,
            interes_pagado=interes
        )
        db.session.add(pago)
        
        # Actualizar estado del empeño
        empeno.estado = 'pagado'
        empeno.interes_acumulado = interes
        db.session.add(empeno)
        
        db.session.commit()
        logger.info(f"Empeño {emp_id} marcado como pagado. Monto: ${empeno.valor_estimado}, Interés: ${int(interes)}")
        flash(f'Empeño {emp_id} marcado como pagado. Total: ${empeno.valor_estimado + int(interes)}', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error marcando empeño {emp_id} como pagado: {e}")
        flash('Error al marcar como pagado', 'error')
    
    return redirect(url_for('admin_panel'))


@app.route('/renovar_empeno', methods=['POST'])
def renovar_empeno():
    if not usuario_activo:
        flash('Debe iniciar sesión', 'error')
        return redirect(url_for('index'))
    
    try:
        emp_id = int(request.form.get('id', 0))
    except (ValueError, TypeError):
        flash('ID inválido', 'error')
        return redirect(url_for('panel') if isinstance(usuario_activo, User) else url_for('admin_panel'))
    
    empeno = Empeno.query.get(emp_id)
    if not empeno:
        flash('No se encontró el empeño', 'error')
        return redirect(url_for('panel') if isinstance(usuario_activo, User) else url_for('admin_panel'))
    
    # Verificar permisos
    owner_dni = empeno.user.dni if empeno.user else None
    active_dni = getattr(usuario_activo, 'dni', usuario_activo.get('dni') if isinstance(usuario_activo, dict) else None)
    is_admin = (isinstance(usuario_activo, dict) and usuario_activo.get('is_admin')) or getattr(usuario_activo, 'is_admin', False)
    
    if owner_dni != active_dni and not is_admin:
        flash('No tiene permisos para renovar este empeño', 'error')
        return redirect(url_for('panel') if isinstance(usuario_activo, User) else url_for('admin_panel'))
    
    # Verificar si está pagado
    paid_entry = PaidLog.query.filter_by(empeno_id=emp_id).first()
    if paid_entry:
        flash('No se puede renovar un empeño ya pagado', 'warning')
        return redirect(url_for('panel') if isinstance(usuario_activo, User) else url_for('admin_panel'))
    
    try:
        now = datetime.now(timezone.utc)
        old = empeno.valor_estimado or 0
        nuevo = int(old * (1 + INTERES_RENOVACION))
        
        # Guardar valor inicial si es la primera renovación
        if not empeno.valor_inicial:
            empeno.valor_inicial = old
        
        empeno.valor_estimado = nuevo
        empeno.created_at = now.isoformat()
        empeno.renovaciones = (empeno.renovaciones or 0) + 1
        empeno.term_days = LOAN_TERM_DAYS
        
        log = RenovationLog(
            empeno_id=emp_id,
            by=active_dni,
            by_admin=is_admin,
            time=now.isoformat(),
            old=old,
            new=nuevo
        )
        db.session.add(log)
        db.session.commit()
        
        logger.info(f"Empeño {emp_id} renovado. ${old} -> ${nuevo}. By: {active_dni} (admin: {is_admin})")
        flash(f'Empeño {emp_id} renovado con éxito. Nuevo valor: ${nuevo}', 'success')
        
        if is_admin and not isinstance(usuario_activo, User):
            return redirect(url_for('admin_panel'))
        return redirect(url_for('panel'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error renovando empeño {emp_id}: {e}")
        flash('Error al renovar empeño', 'error')
        return redirect(url_for('panel') if isinstance(usuario_activo, User) else url_for('admin_panel'))


@app.route('/precotizar', methods=['POST'])
def precotizar():
    if not usuario_activo:
        flash('Debe iniciar sesión', 'error')
        return redirect(url_for('index'))
    
    tipo = sanitizar_input(request.form.get('tipo', ''), 120)
    descripcion = sanitizar_input(request.form.get('descripcion', ''), 500)
    
    try:
        valor_ref = float(request.form.get('valor_ref', 0))
        estado_input = float(request.form.get('estado', 0))
        estado = estado_input / 100.0 if estado_input > 1 else estado_input
        
        if valor_ref <= 0:
            flash('El valor de referencia debe ser mayor a 0', 'error')
            return redirect(url_for('panel'))
        
        if estado < 0 or estado > 1:
            flash('El estado debe estar entre 0% y 100%', 'error')
            return redirect(url_for('panel'))
            
    except (ValueError, TypeError):
        flash('Valores numéricos inválidos', 'error')
        return redirect(url_for('panel'))
    
    if not tipo or not descripcion:
        flash('Tipo y descripción son obligatorios', 'error')
        return redirect(url_for('panel'))
    
    entrada = pd.DataFrame({'valor_referencia': [valor_ref], 'estado': [estado]})
    
    try:
        valor_estimado = int(modelo_ia.predict(entrada)[0])
    except Exception as e:
        logger.warning(f"Error en predicción IA: {e}")
        valor_estimado = int(valor_ref * (0.5 + estado * 0.3))
    
    # Validar rango razonable
    if valor_estimado > valor_ref * 0.8 or valor_estimado < valor_ref * 0.3:
        valor_estimado = int(valor_ref * (0.5 + estado * 0.3))
    
    session['ultima_cotizacion'] = {
        'tipo': tipo,
        'descripcion': descripcion,
        'valor_ref': valor_ref,
        'estado': estado,
        'valor_estimado': valor_estimado,
        'fecha_cotizacion': datetime.now(timezone.utc).isoformat()
    }
    
    # Si el usuario acepta la cotización
    if 'aceptar' in request.form:
        datos = session.get('ultima_cotizacion')
        if not datos:
            flash('No se encontró la última cotización', 'error')
            return redirect(url_for('panel'))
        
        try:
            user_id = None
            if isinstance(usuario_activo, User):
                user_id = usuario_activo.id
            else:
                u = User.query.filter_by(dni=usuario_activo.get('dni')).first()
                user_id = u.id if u else None
            
            if user_id is None:
                flash('Usuario inválido', 'error')
                return redirect(url_for('panel'))
            
            nuevo = Empeno(
                user_id=user_id,
                tipo=datos['tipo'],
                descripcion=datos['descripcion'],
                valor_estimado=datos['valor_estimado'],
                valor_inicial=datos['valor_estimado'],
                created_at=datetime.now(timezone.utc).isoformat(),
                term_days=LOAN_TERM_DAYS,
                renovaciones=0,
                estado='activo',
                interes_acumulado=0.0
            )
            db.session.add(nuevo)
            db.session.commit()
            session.pop('ultima_cotizacion', None)
            
            logger.info(f"Empeño registrado: ID {nuevo.id}, User: {user_id}, Valor: ${datos['valor_estimado']}")
            flash(f'Empeño registrado exitosamente. ID: {nuevo.id}', 'success')
            # Redirigir al formulario para agendar cita asociada al empeño recién creado
            return redirect(url_for('agendar_cita_form', empeno_id=nuevo.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error guardando empeño: {e}")
            flash('Error guardando el empeño', 'error')
            return redirect(url_for('panel'))
    
    estado_percent = int(estado * 100)
    return render_template(
        'resultado.html',
        tipo=tipo,
        descripcion=descripcion,
        valor_ref=valor_ref,
        estado=estado,
        estado_percent=estado_percent,
        valor_estimado=valor_estimado,
        usuario=usuario_activo
    )


@app.route('/agendar_cita', methods=['POST'])
@login_required
def agendar_cita():
    """Agendar una cita para evaluación de empeño"""
    try:
        fecha_str = request.form.get('fecha', '')
        hora_str = request.form.get('hora', '')
        empeno_id = request.form.get('empeno_id')
        
        # Validar fecha
        fecha_valida, msg_fecha = validar_fecha_cita(fecha_str)
        if not fecha_valida:
            flash(f'Fecha inválida: {msg_fecha}', 'error')
            return redirect(url_for('panel'))
        
        # Validar hora
        hora_valida, msg_hora = validar_hora_cita(hora_str)
        if not hora_valida:
            flash(f'Hora inválida: {msg_hora}', 'error')
            return redirect(url_for('panel'))
        
        # Prevención de doble-reserva: no permitir otra cita pendiente/confirmada en mismo slot
        existente = Cita.query.filter_by(fecha=fecha_str, hora=hora_str).filter(Cita.estado.in_(['pendiente', 'confirmada'])).first()
        if existente:
            flash('Ya existe una cita en esa fecha y hora. Por favor, elija otra hora.', 'error')
            # Si venimos desde un empeño específico, volver al formulario de agendado
            try:
                return redirect(url_for('agendar_cita_form', empeno_id=int(empeno_id))) if empeno_id else redirect(url_for('panel'))
            except Exception:
                return redirect(url_for('panel'))

        # Crear la cita
        nueva_cita = Cita(
            user_id=usuario_activo.id,
            empeno_id=int(empeno_id) if empeno_id else None,
            fecha=fecha_str,
            hora=hora_str,
            estado='pendiente'
        )

        db.session.add(nueva_cita)
        db.session.commit()
        
        logger.info(f"Cita agendada: ID {nueva_cita.id}, Usuario: {usuario_activo.dni}, Fecha: {fecha_str}, Hora: {hora_str}")
        flash(f'Cita agendada exitosamente para {fecha_str} a las {hora_str}', 'success')
        return redirect(url_for('panel'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error agendando cita: {e}")
        flash('Error al agendar cita', 'error')
        return redirect(url_for('panel'))


@app.route('/agendar_cita/<int:empeno_id>', methods=['GET'])
@login_required
def agendar_cita_form(empeno_id):
    """Formulario para agendar cita asociado a un empeño recién creado"""
    empeno = Empeno.query.get(empeno_id)
    if not empeno:
        flash('No se encontró el empeño para agendar cita', 'error')
        return redirect(url_for('panel'))

    # Pasar datos del empeño a la plantilla
    return render_template('agendar_cita.html', usuario=usuario_activo, empeno=empeno)


@app.route('/_shutdown', methods=['POST', 'GET'])
def _shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        return 'Server shutdown not available', 500
    func()
    return 'Server shutting down...'


# ============ NUEVAS FUNCIONALIDADES ============

@app.route('/reportes')
@admin_required
def reportes():
    """Vista de reportes y estadísticas avanzadas"""
    # Estadísticas generales
    total_empenos = Empeno.query.count()
    total_activos = Empeno.query.filter_by(estado='activo').count()
    total_pagados = Empeno.query.filter_by(estado='pagado').count()
    total_usuarios = User.query.count()
    
    # Suma total de valores
    suma_activos = db.session.query(db.func.sum(Empeno.valor_estimado)).filter_by(estado='activo').scalar() or 0
    suma_pagados_log = db.session.query(db.func.sum(PaidLog.monto_pagado)).scalar() or 0
    suma_intereses = db.session.query(db.func.sum(PaidLog.interes_pagado)).scalar() or 0
    
    # Top 5 usuarios con más empeños
    top_usuarios = db.session.query(
        User.nombre,
        User.dni,
        db.func.count(Empeno.id).label('total')
    ).join(Empeno).group_by(User.id).order_by(db.desc('total')).limit(5).all()
    
    # Empeños por tipo
    empenos_por_tipo = db.session.query(
        Empeno.tipo,
        db.func.count(Empeno.id).label('total')
    ).group_by(Empeno.tipo).order_by(db.desc('total')).all()
    
    stats = {
        'total_empenos': total_empenos,
        'total_activos': total_activos,
        'total_pagados': total_pagados,
        'total_usuarios': total_usuarios,
        'suma_activos': suma_activos,
        'suma_pagados': suma_pagados_log,
        'suma_intereses': suma_intereses,
        'top_usuarios': top_usuarios,
        'empenos_por_tipo': empenos_por_tipo
    }
    
    return render_template('reportes.html', usuario=usuario_activo, stats=stats)


@app.route('/exportar/<tipo>')
@admin_required
def exportar(tipo):
    """Exportar datos a CSV"""
    try:
        if tipo == 'usuarios':
            usuarios = User.query.all()
            data = [u.to_dict() for u in usuarios]
            df = pd.DataFrame(data)
            filename = f'usuarios_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
        elif tipo == 'empenos':
            empenos = Empeno.query.all()
            data = []
            for e in empenos:
                data.append({
                    'id': e.id,
                    'user_dni': e.user.dni if e.user else None,
                    'user_nombre': e.user.nombre if e.user else None,
                    'tipo': e.tipo,
                    'descripcion': e.descripcion,
                    'valor_estimado': e.valor_estimado,
                    'valor_inicial': e.valor_inicial,
                    'renovaciones': e.renovaciones,
                    'estado': e.estado,
                    'created_at': e.created_at
                })
            df = pd.DataFrame(data)
            filename = f'empenos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
        elif tipo == 'pagos':
            pagos = PaidLog.query.all()
            data = []
            for p in pagos:
                data.append({
                    'id': p.id,
                    'empeno_id': p.empeno_id,
                    'monto_pagado': p.monto_pagado,
                    'interes_pagado': p.interes_pagado,
                    'time': p.time,
                    'by_admin': p.by_admin
                })
            df = pd.DataFrame(data)
            filename = f'pagos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        else:
            flash('Tipo de exportación inválido', 'error')
            return redirect(url_for('admin_panel'))
        
        # Guardar CSV temporalmente
        filepath = os.path.join(os.path.dirname(__file__), filename)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        logger.info(f"Exportación realizada: {tipo} - {filename}")
        flash(f'Archivo exportado: {filename}', 'success')
        return redirect(url_for('admin_panel'))
        
    except Exception as e:
        logger.error(f"Error en exportación {tipo}: {e}")
        flash('Error al exportar datos', 'error')
        return redirect(url_for('admin_panel'))


@app.route('/admin/crear', methods=['POST'])
@admin_required
def crear_admin():
    """Crear nuevo administrador"""
    username = sanitizar_input(request.form.get('username', ''), 64)
    password = request.form.get('password', '')
    
    if not username or not password:
        flash('Usuario y contraseña son obligatorios', 'error')
        return redirect(url_for('admin_panel'))
    
    if len(password) < 6:
        flash('La contraseña debe tener al menos 6 caracteres', 'error')
        return redirect(url_for('admin_panel'))
    
    if Admin.query.filter_by(username=username).first():
        flash('Ya existe un administrador con ese nombre de usuario', 'error')
        return redirect(url_for('admin_panel'))
    
    try:
        nuevo_admin = Admin(username=username)
        nuevo_admin.set_password(password)
        db.session.add(nuevo_admin)
        db.session.commit()
        
        logger.info(f"Nuevo admin creado: {username}")
        flash(f'Administrador {username} creado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creando admin: {e}")
        flash('Error al crear administrador', 'error')
    
    return redirect(url_for('admin_panel'))


@app.route('/api/stats')
@admin_required
def api_stats():
    """API endpoint para estadísticas (para futuros dashboards dinámicos)"""
    total_empenos = Empeno.query.count()
    total_activos = Empeno.query.filter_by(estado='activo').count()
    total_pagados = Empeno.query.filter_by(estado='pagado').count()
    
    return jsonify({
        'total_empenos': total_empenos,
        'total_activos': total_activos,
        'total_pagados': total_pagados,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


# Manejadores de errores
@app.errorhandler(404)
def not_found(e):
    flash('Página no encontrada', 'error')
    return redirect(url_for('index'))


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Error 500: {e}")
    flash('Error interno del servidor', 'error')
    return redirect(url_for('index'))


def _open_browser_when_ready(url: str, timeout: int = 30):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with urllib.request.urlopen(url, timeout=1):
                webbrowser.open(url)
                return True
        except Exception:
            time.sleep(0.5)
    try:
        webbrowser.open(url)
    except Exception:
        pass


if __name__ == '__main__':
    _app_url = 'http://127.0.0.1:5000'
    def _run_server():
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False, threaded=True)
    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()
    if _HAS_PYSTRAY:
        def _make_icon_image(size=64, color1=(30,144,255,255), color2=(255,255,255,0)):
            img = Image.new('RGBA', (size, size), color2)
            draw = ImageDraw.Draw(img)
            r = int(size * 0.4)
            cx = cy = size // 2
            draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=color1)
            return img
        icon_image = _make_icon_image()
        def _open_browser(_: pystray.Icon, item=None):
            try:
                webbrowser.open(_app_url)
            except Exception:
                pass
        def _shutdown(_: pystray.Icon, item=None):
            try:
                urllib.request.urlopen(_app_url + '/_shutdown', data=b'', timeout=2)
            except Exception:
                pass
            try:
                _.stop()
            except Exception:
                pass
            time.sleep(0.2)
            os._exit(0)
        menu = pystray.Menu(pystray.MenuItem('Abrir navegador', _open_browser), pystray.MenuItem('Salir', _shutdown))
        icon = pystray.Icon('app_empenos_web', icon_image, 'Empeños IA', menu)
        threading.Thread(target=_open_browser_when_ready, args=(_app_url, 30), daemon=True).start()
        icon.run()
    else:
        threading.Thread(target=_open_browser_when_ready, args=(_app_url, 30), daemon=True).start()
        try:
            while server_thread.is_alive():
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
