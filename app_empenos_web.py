"""app_empenos_web.py
Versión compacta y estable reconstruida: Flask + SQLite (SQLAlchemy) + pequeño modelo IA.
Mantiene las rutas: index, registrar, login, logout, panel, admin_login, admin_panel,
rechazar_empeno, renovar_empeno, precotizar y _shutdown. Soporta pystray opcional.
"""
import os
import sys
import threading
import webbrowser
import time
import urllib.request
from datetime import datetime, timezone, timedelta

from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

try:
    import pystray
    from PIL import Image, ImageDraw
    _HAS_PYSTRAY = True
except Exception:
    _HAS_PYSTRAY = False

template_folder = (
    os.path.join(sys._MEIPASS, 'templates')
    if getattr(sys, 'frozen', False)
    else os.path.join(os.path.dirname(__file__), 'templates')
)

app = Flask(__name__, template_folder=template_folder)
app.secret_key = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
    def to_dict(self):
        return {'id': self.id, 'nombre': self.nombre, 'dni': self.dni}


class Empeno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tipo = db.Column(db.String(120))
    descripcion = db.Column(db.String(500))
    valor_estimado = db.Column(db.Integer)
    created_at = db.Column(db.String(64))
    term_days = db.Column(db.Integer, default=30)
    renovaciones = db.Column(db.Integer, default=0)
    user = db.relationship('User', backref=db.backref('empenos', lazy=True))


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



with app.app_context():
    db.create_all()


usuario_activo = None
LOAN_TERM_DAYS = 30
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'


@app.route('/')
def index():
    return render_template('index.html', usuario=usuario_activo)


@app.route('/registrar', methods=['POST'])
def registrar():
    nombre = request.form['nombre']
    dni = request.form['dni']
    try:
        nuevo = User(nombre=nombre, dni=dni)
        db.session.add(nuevo)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return render_template('index.html', error='Ya existe un usuario con ese DNI', usuario=None)
    return render_template('index.html', msg=f'Usuario {nombre} registrado con éxito.', usuario=None)


@app.route('/login', methods=['POST'])
def login():
    global usuario_activo
    dni = request.form['dni']
    user = User.query.filter_by(dni=dni).first()
    if user:
        usuario_activo = user
        return redirect(url_for('panel'))
    return render_template('index.html', error='Usuario no encontrado.', usuario=None)


@app.route('/logout')
def logout():
    global usuario_activo
    usuario_activo = None
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
def panel():
    if not usuario_activo or not isinstance(usuario_activo, User):
        return redirect(url_for('index'))
    historial = []
    for e in Empeno.query.filter_by(user_id=usuario_activo.id).all():
        left, exp = _days_left(e.created_at, e.term_days or LOAN_TERM_DAYS)
        # comprobar pago en el log
        paid_entry = PaidLog.query.filter_by(empeno_id=e.id).order_by(PaidLog.time.desc()).first()
        pagado = bool(paid_entry)
        pagado_at = paid_entry.time if paid_entry else None
        historial.append({'id': e.id, 'tipo': e.tipo, 'descripcion': e.descripcion, 'valor_estimado': e.valor_estimado, 'renovaciones': e.renovaciones, 'created_at': e.created_at, 'term_days': e.term_days, 'dias_restantes': left, 'expiracion': exp, 'pagado': pagado, 'pagado_at': pagado_at})
    return render_template('panel.html', usuario=usuario_activo, historial=historial, msg=request.args.get('msg'), error=request.args.get('err'))


@app.route('/admin_login', methods=['POST'])
def admin_login():
    global usuario_activo
    username = request.form.get('admin_user', '')
    password = request.form.get('admin_pass', '')
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        usuario_activo = {'nombre': 'Administrador', 'dni': 'admin', 'is_admin': True}
        return redirect(url_for('admin_panel'))
    return render_template('index.html', error='Credenciales de administrador incorrectas.', usuario=None)


@app.route('/admin_panel')
def admin_panel():
    if not usuario_activo or not usuario_activo.get('is_admin'):
        return render_template('index.html', error='Acceso restringido. Inicia sesión como admin.', usuario=None)
    enriched = []
    for e in Empeno.query.all():
        left, exp = _days_left(e.created_at, e.term_days or LOAN_TERM_DAYS)
        paid_entry = PaidLog.query.filter_by(empeno_id=e.id).order_by(PaidLog.time.desc()).first()
        pagado = bool(paid_entry)
        pagado_at = paid_entry.time if paid_entry else None
        enriched.append({'id': e.id, 'dni': e.user.dni if e.user else None, 'tipo': e.tipo, 'descripcion': e.descripcion, 'valor_estimado': e.valor_estimado, 'renovaciones': e.renovaciones, 'created_at': e.created_at, 'term_days': e.term_days, 'expiracion': exp, 'pagado': pagado, 'pagado_at': pagado_at})
    users_db = User.query.all()
    renov_log = RenovationLog.query.order_by(RenovationLog.time.desc()).all()
    pagos_log = PaidLog.query.order_by(PaidLog.time.desc()).all()
    return render_template('admin.html', usuario=usuario_activo, usuarios=users_db, empenos=enriched, msg=request.args.get('msg'), error=request.args.get('err'), renovaciones_log=renov_log, pagos_log=pagos_log)


@app.route('/rechazar_empeno', methods=['POST'])
def rechazar_empeno():
    if not usuario_activo or not usuario_activo.get('is_admin'):
        return render_template('index.html', error='Acceso restringido. Inicia sesión como admin.', usuario=None)
    try:
        id_str = request.form.get('id')
        if id_str is None:
            return redirect(url_for('admin_panel', err='ID inválido'))
        emp_id = int(id_str)
    except ValueError:
        return redirect(url_for('admin_panel', err='ID inválido'))
    target = Empeno.query.get(emp_id)
    if not target:
        return redirect(url_for('admin_panel', err=f'No se encontró empeño con ID {emp_id}'))
    if target.renovaciones and target.renovaciones > 0:
        return redirect(url_for('admin_panel', err=f'No se puede rechazar el empeño {emp_id} porque fue renovado'))
    db.session.delete(target)
    db.session.commit()
    return redirect(url_for('admin_panel', msg=f'Empeño {emp_id} rechazado y eliminado'))


@app.route('/marcar_pagado', methods=['POST'])
def marcar_pagado():
    # Solo admin puede marcar como pagado
    if not usuario_activo or not usuario_activo.get('is_admin'):
        return render_template('index.html', error='Acceso restringido. Inicia sesión como admin.', usuario=None)
    try:
        id_str = request.form.get('id')
        if id_str is None:
            return redirect(url_for('admin_panel', err='ID inválido'))
        emp_id = int(id_str)
    except ValueError:
        return redirect(url_for('admin_panel', err='ID inválido'))
    empeno = Empeno.query.get(emp_id)
    if not empeno:
        return redirect(url_for('admin_panel', err=f'No se encontró empeño con ID {emp_id}'))
    # Registrar pago en PaidLog
    now = datetime.now(timezone.utc).isoformat()
    pago = PaidLog(empeno_id=emp_id, by_admin=True, time=now)
    db.session.add(pago)

    # Intentar revertir la última renovación si existe (cancelar renovación)
    last_ren = RenovationLog.query.filter_by(empeno_id=emp_id).order_by(RenovationLog.time.desc()).first()
    canceled = False
    if last_ren:
        try:
            # revertir valor y decrementar contador de renovaciones
            empeno.valor_estimado = last_ren.old if last_ren.old is not None else empeno.valor_estimado
            empeno.renovaciones = (empeno.renovaciones or 1) - 1
            if empeno.renovaciones < 0:
                empeno.renovaciones = 0
            db.session.add(empeno)
            canceled = True
        except Exception:
            # no crítico, continuar
            canceled = False

    db.session.commit()
    msg = f'Empeño {emp_id} marcado como pagado'
    if canceled:
        msg += ' y se revirtió la última renovación'
    return redirect(url_for('admin_panel', msg=msg))


@app.route('/renovar_empeno', methods=['POST'])
def renovar_empeno():
    if not usuario_activo:
        return redirect(url_for('index'))
    try:
        id_str = request.form.get('id')
        if id_str is None:
            return redirect(url_for('panel'))
        emp_id = int(id_str)
    except ValueError:
        return redirect(url_for('panel'))
    now = datetime.now(timezone.utc)
    empeno = Empeno.query.get(emp_id)
    if not empeno:
        return redirect(url_for('panel', err='No se encontró el empeño o no tiene permisos'))
    owner_dni = empeno.user.dni if empeno.user else None
    active_dni = getattr(usuario_activo, 'dni', usuario_activo.get('dni') if isinstance(usuario_activo, dict) else None)
    is_admin = (isinstance(usuario_activo, dict) and usuario_activo.get('is_admin')) or getattr(usuario_activo, 'is_admin', False)
    if owner_dni == active_dni or is_admin:
        old = empeno.valor_estimado or 0
        nuevo = int(old * 1.05)
        empeno.valor_estimado = nuevo
        empeno.created_at = now.isoformat()
        empeno.renovaciones = (empeno.renovaciones or 0) + 1
        log = RenovationLog(empeno_id=emp_id, by=active_dni, by_admin=is_admin, time=now.isoformat(), old=old, new=nuevo)
        db.session.add(log)
        db.session.commit()
        if is_admin:
            return redirect(url_for('admin_panel', msg=f'Empeño {emp_id} renovado por admin'))
        return redirect(url_for('panel', msg=f'Empeño {emp_id} renovado.'))
    return redirect(url_for('panel', err='No se encontró el empeño o no tiene permisos'))


@app.route('/precotizar', methods=['POST'])
def precotizar():
    if not usuario_activo:
        return redirect(url_for('index'))
    tipo = request.form.get('tipo', '')
    descripcion = request.form.get('descripcion', '')
    try:
        valor_ref = float(request.form.get('valor_ref', 0))
        estado_input = float(request.form.get('estado', 0))
        estado = estado_input / 100.0 if estado_input > 1 else estado_input
    except ValueError:
        return redirect(url_for('panel', err='Valores numéricos inválidos'))
    entrada = pd.DataFrame({'valor_referencia': [valor_ref], 'estado': [estado]})
    try:
        valor_estimado = int(modelo_ia.predict(entrada)[0])
    except Exception:
        valor_estimado = int(valor_ref * (0.5 + estado * 0.3))
    if valor_estimado > valor_ref * 0.8 or valor_estimado < valor_ref * 0.5:
        valor_estimado = int(valor_ref * (0.5 + estado * 0.3))
    session['ultima_cotizacion'] = {'tipo': tipo, 'descripcion': descripcion, 'valor_ref': valor_ref, 'estado': estado, 'valor_estimado': valor_estimado}
    if 'aceptar' in request.form:
        datos = session.get('ultima_cotizacion')
        if datos:
            try:
                user_id = None
                if isinstance(usuario_activo, User):
                    user_id = usuario_activo.id
                else:
                    u = User.query.filter_by(dni=usuario_activo.get('dni')).first()
                    user_id = u.id if u else None
                if user_id is None:
                    return redirect(url_for('panel', err='Usuario inválido'))
                nuevo = Empeno(user_id=user_id, tipo=datos['tipo'], descripcion=datos['descripcion'], valor_estimado=datos['valor_estimado'], created_at=datetime.now(timezone.utc).isoformat(), term_days=LOAN_TERM_DAYS, renovaciones=0)
                db.session.add(nuevo)
                db.session.commit()
                session.pop('ultima_cotizacion', None)
                return redirect(url_for('panel'))
            except Exception:
                db.session.rollback()
                return redirect(url_for('panel', err='Error guardando el empeño'))
        else:
            return redirect(url_for('panel', err='No se encontró la última cotización'))
    estado_percent = int(estado * 100)
    return render_template('resultado.html', tipo=tipo, descripcion=descripcion, valor_ref=valor_ref, estado=estado, estado_percent=estado_percent, valor_estimado=valor_estimado, usuario=usuario_activo)


@app.route('/_shutdown', methods=['POST', 'GET'])
def _shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        return 'Server shutdown not available', 500
    func()
    return 'Server shutting down...'


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
