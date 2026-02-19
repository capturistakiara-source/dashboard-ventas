import os
import json
import re
import sqlite3
import unicodedata
import uuid
import gspread
import time
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, flash, session
from google.oauth2.service_account import Credentials
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from dotenv import load_dotenv, find_dotenv
import pytz
import csv
import io
from flask import send_file
from functools import wraps
from flask import abort
from flask import Flask, render_template, url_for

# ==================== CONFIGURACION INICIAL ====================
app = Flask(__name__)
app.secret_key = 'Lapostal01'

# ConfiguraciÃ³n de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesiÃ³n para acceder a esta pÃ¡gina.'

# USUARIOS - CONTRASEÑAS EN TEXTO PLANO
USUARIOS = {
    'C.E.O': {
        'password': 'Dpostal01',
        'nombre': 'Merlin Lara Arturo',
        'rol': 'C.E.O'
    },
    'Direccion': {
        'password': 'Dpostal01',
        'nombre': 'Pedraza Jose Luis',
        'rol': 'C.E.O'
    },
    'Gerente Operativo': {
        'password': 'GOpostal01',
        'nombre': 'Campa Badachi Salvador ',
        'rol': 'Gerente Operativo'
    },
    'Gerente operaciones': {
        'password': 'GOpostal01',
        'nombre': 'Francisco Conrado Osuna ',
        'rol': 'Gerente operaciones'
    },
    'Capacitador de Gerentes': {
        'password': 'CGpostal01',
        'nombre': 'SÃ¡nchez Rangel Carlos Javier',
        'rol': 'Capacitador de Gerentes'
    },
    'Gerente AdministraciÃ³n': {
        'password': 'GApostal01',
        'nombre': 'Abaroa Esqueda Leonardo',
        'rol': 'Gerente AdministraciÃ³n'
    },
    'Gerente Regional': {
        'password': 'GRpostal01',
        'nombre': 'Garcia Vinalay Jairo Isait',
        'rol': 'Gerente Regional'
    },
    'Planeacion': {
        'password': 'Ppostal01',
        'nombre': 'Ramos Contreras Omar Antonio',
        'rol': 'Planeacion'
    },
    'Gerente Mkt': {
        'password': 'GMpostal01',
        'nombre': 'Franco Alonzo Jesus Omar',
        'rol': 'Gerente Mkt'
    },
    'Chef Ejecutivo': {
        'password': 'CEpostal01',
        'nombre': 'Casillas Martinez Angel Alberto',
        'rol': 'Chef Ejecutivo'
    },
    'Gerente Sistemas': {
        'password': 'Lapostal01',
        'nombre': 'Santiago Ortega Joel',
        'rol': 'Gerente Sistemas'
    },
    'Gerente Recursos Humanos': {
        'password': 'GRHpostal01',
        'nombre': 'Garcia Rodriguez Genesis Clarise',
        'rol': 'Gerente RH'
    },
    'Licenciado': {
        'password': 'Lcapostal01',
        'nombre': 'Martinez Peralta Christian Ignacio',
        'rol': ''
    },
    'Gerentes': {
        'password': 'Gpostal01',
        'nombre': 'Sucursales',
        'rol': 'Gerencia Sucursales'
    }
}

SUPERVISION_SUCURSALES = [
    "BRISAS",
    "CACHO",
    "ENSENADA",
    "MATRIZ",
    "PLAYAS 1",
    "TORRES",
    "DARUMMITA PLAYAS",
    "ROSARITO 3",
    "5 Y 10",
    "ALEMAN",
    "CALIFORNIAS",
    "CAMPESTRE MURUA",
    "CAMPIÑA",
    "CAPISTRANO",
    "COLINA AZUL",
    "DARUMMITA LIBERTAD",
    "FLORIDO",
    "INDEPENDENCIA",
    "LAGO",
    "LIBERTAD",
    "MARIANO MATAMOROS",
    "MURUA",
    "PANAMERICANO",
    "SOLER",
    "VENECIA",
    "ZONA NORTE",
    "ZONA RIO",
    "ALBA ROJA",
    "ALTIPLANO",
    "BELLAS ARTES",
    "BUENOS AIRES",
    "CAMINO VERDE",
    "CASA BLANCA",
    "CLINICA 1",
    "CUCAPAH",
    "DARUMMITA CALIFORNIAS",
    "DARUMMITA MARIANO MATAMOROS",
    "DARUMMITA TECNOLOGICO",
    "DELICIAS",
    "EL AGUILA",
    "FLAMINGOS",
    "FUNDADORES",
    "GLORIA",
    "GRAN FLORIDO",
    "HUERTAS",
    "JARDIN DORADO",
    "JIBARITO/FLORES MAGON",
    "LOMA BONITA",
    "MALECON",
    "MALECON 2",
    "MESA / PENI",
    "MIRADOR",
    "NATURA",
    "OASIS",
    "OTAY CONSTITUYENTES",
    "PACIFICO",
    "PANAMERICANO II",
    "PLAYAS 2",
    "PRESA",
    "RIO BRAVO",
    "ROSARITO 1",
    "ROSARITO 2 NORTE",
    "RUBI",
    "SANTA FE",
    "TECNOLOGICO",
    "UABC",
    "URBI VILLA DEL PRADO",
    "VILLA FLORESTA",
    "VILLA FONTANA",
    "VILLAS DEL CAMPO, ERMITA Y 20 NOV",
]

SUPERVISION_USUARIOS = [
    {"value": "supervisor1", "label": "Supervisor 1"},
    {"value": "supervisor2", "label": "Supervisor 2"},
    {"value": "supervisor3", "label": "Supervisor 3"},
]

SUPERVISION_DB_PATH = os.path.join(os.path.dirname(__file__), "supervision_visitas.db")
SUPERVISION_UPLOAD_ROOT = os.path.join("static", "uploads", "supervision")
SUPERVISION_UPLOAD_SUPERVISOR_DIR = os.path.join(SUPERVISION_UPLOAD_ROOT, "supervisores")
SUPERVISION_UPLOAD_SUCURSAL_DIR = os.path.join(SUPERVISION_UPLOAD_ROOT, "sucursales")
TZ_TIJUANA = pytz.timezone("America/Tijuana")

class User(UserMixin):
    def __init__(self, id, nombre, rol):
        self.id = id
        self.nombre = nombre
        self.rol = rol

@login_manager.user_loader
def load_user(user_id):
    if user_id in USUARIOS:
        user_data = USUARIOS[user_id]
        return User(user_id, user_data['nombre'], user_data['rol'])
    return None

def only_users(*allowed_user_ids):
    """
    Permite acceso SOLO a los user.id indicados.
    Ej: @only_users('Gerentes')
    """
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.id not in allowed_user_ids:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def _normalizar_texto_password(texto):
    limpio = str(texto or "")
    limpio = "".join(c for c in unicodedata.normalize("NFD", limpio) if unicodedata.category(c) != "Mn")
    limpio = limpio.lower()
    limpio = re.sub(r"[^a-z0-9]+", "", limpio)
    return limpio


def _contrasena_supervision(valor_usuario):
    return f"Lp{_normalizar_texto_password(valor_usuario)}"


def _init_supervision_storage():
    os.makedirs(SUPERVISION_UPLOAD_SUPERVISOR_DIR, exist_ok=True)
    os.makedirs(SUPERVISION_UPLOAD_SUCURSAL_DIR, exist_ok=True)


def _init_supervision_db():
    _init_supervision_storage()
    with sqlite3.connect(SUPERVISION_DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS supervision_ingresos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingreso_at TEXT NOT NULL,
                ingreso_fecha TEXT NOT NULL,
                ingreso_semana TEXT NOT NULL,
                dashboard_user TEXT NOT NULL,
                supervisor TEXT NOT NULL,
                sucursal TEXT NOT NULL,
                foto_supervisor TEXT NOT NULL,
                foto_sucursal TEXT NOT NULL
            )
            """
        )


def _guardar_foto_supervision(archivo, carpeta_destino, prefijo):
    if not archivo or not archivo.filename:
        return None

    nombre_seguro = secure_filename(archivo.filename)
    extension = os.path.splitext(nombre_seguro)[1].lower()
    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        return None

    nombre_final = f"{prefijo}_{uuid.uuid4().hex}{extension}"
    ruta_relativa = os.path.join(carpeta_destino, nombre_final).replace("\\", "/")
    ruta_absoluta = os.path.join(os.path.dirname(__file__), ruta_relativa)
    os.makedirs(os.path.dirname(ruta_absoluta), exist_ok=True)
    archivo.save(ruta_absoluta)
    return ruta_relativa


def _registrar_ingreso_supervision(ingreso_at, dashboard_user, supervisor, sucursal, foto_supervisor, foto_sucursal):
    ingreso_fecha = ingreso_at.strftime("%Y-%m-%d")
    ingreso_semana = f"{ingreso_at.isocalendar().year}-W{ingreso_at.isocalendar().week:02d}"

    with sqlite3.connect(SUPERVISION_DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO supervision_ingresos
            (ingreso_at, ingreso_fecha, ingreso_semana, dashboard_user, supervisor, sucursal, foto_supervisor, foto_sucursal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ingreso_at.isoformat(),
                ingreso_fecha,
                ingreso_semana,
                dashboard_user,
                supervisor,
                sucursal,
                foto_supervisor,
                foto_sucursal,
            ),
        )
        return cursor.lastrowid


def _obtener_estadisticas_supervision():
    ahora_tj = datetime.now(TZ_TIJUANA)
    hoy = ahora_tj.strftime("%Y-%m-%d")
    semana_actual = f"{ahora_tj.isocalendar().year}-W{ahora_tj.isocalendar().week:02d}"

    with sqlite3.connect(SUPERVISION_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        visitas_semana = conn.execute(
            """
            SELECT
                sucursal,
                COUNT(*) AS total_visitas,
                GROUP_CONCAT(DISTINCT supervisor) AS supervisores
            FROM supervision_ingresos
            WHERE ingreso_semana = ?
            GROUP BY sucursal
            ORDER BY total_visitas DESC, sucursal ASC
            """,
            (semana_actual,),
        ).fetchall()

        visitas_usuario_hoy = conn.execute(
            """
            SELECT
                supervisor,
                COUNT(*) AS total_sucursales,
                GROUP_CONCAT(sucursal) AS sucursales
            FROM supervision_ingresos
            WHERE ingreso_fecha = ?
            GROUP BY supervisor
            ORDER BY total_sucursales DESC, supervisor ASC
            """,
            (hoy,),
        ).fetchall()

        ingresos_recientes = conn.execute(
            """
            SELECT
                ingreso_at,
                dashboard_user,
                supervisor,
                sucursal
            FROM supervision_ingresos
            ORDER BY id DESC
            LIMIT 100
            """
        ).fetchall()

    return {
        "hoy": hoy,
        "semana_actual": semana_actual,
        "visitas_semana": [dict(fila) for fila in visitas_semana],
        "visitas_usuario_hoy": [dict(fila) for fila in visitas_usuario_hoy],
        "ingresos_recientes": [dict(fila) for fila in ingresos_recientes],
    }


def _obtener_panel_hoja_visita(supervisor):
    hoy = datetime.now(TZ_TIJUANA).date()
    hace_7 = (hoy - timedelta(days=6)).strftime("%Y-%m-%d")
    hoy_str = hoy.strftime("%Y-%m-%d")

    with sqlite3.connect(SUPERVISION_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        visitas_7_dias = conn.execute(
            """
            SELECT
                sucursal,
                COUNT(*) AS visitas,
                GROUP_CONCAT(DISTINCT supervisor) AS usuarios
            FROM supervision_ingresos
            WHERE ingreso_fecha >= ?
            GROUP BY sucursal
            ORDER BY visitas DESC, sucursal ASC
            """,
            (hace_7,),
        ).fetchall()

        visitas_usuario_hoy = conn.execute(
            """
            SELECT
                supervisor,
                COUNT(*) AS visitas
            FROM supervision_ingresos
            WHERE ingreso_fecha = ?
            GROUP BY supervisor
            ORDER BY visitas DESC, supervisor ASC
            """,
            (hoy_str,),
        ).fetchall()

        ultima_visita_supervisor = conn.execute(
            """
            SELECT sucursal
            FROM supervision_ingresos
            WHERE supervisor = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (supervisor,),
        ).fetchone()

        ingresos_recientes = conn.execute(
            """
            SELECT
                ingreso_at,
                supervisor,
                sucursal
            FROM supervision_ingresos
            ORDER BY id DESC
            LIMIT 20
            """
        ).fetchall()

    ingresos_formateados = []
    for fila in ingresos_recientes:
        registro = dict(fila)
        try:
            fecha_dt = datetime.fromisoformat(registro["ingreso_at"])
            if fecha_dt.tzinfo is not None:
                fecha_dt = fecha_dt.astimezone(TZ_TIJUANA)
            registro["ingreso_fecha_hora"] = fecha_dt.strftime("%d/%m/%Y %I:%M %p")
        except Exception:
            registro["ingreso_fecha_hora"] = registro["ingreso_at"]
        ingresos_formateados.append(registro)

    return {
        "visitas_7_dias": [dict(fila) for fila in visitas_7_dias],
        "visitas_usuario_hoy": [dict(fila) for fila in visitas_usuario_hoy],
        "ultima_sucursal": (dict(ultima_visita_supervisor)["sucursal"] if ultima_visita_supervisor else "-"),
        "ingresos_recientes": ingresos_formateados,
    }


_init_supervision_db()

# ==================== AUTENTICACIÃ“N GOOGLE ====================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
load_dotenv(find_dotenv())
SHEET_NAME = os.getenv("SHEET_NAME")
GOOGLE_CREDS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")

if not GOOGLE_CREDS_FILE:
    raise RuntimeError("âŒ La informacion de google_credentials.json no se encuentra disponible")

try:
    creds_data = json.loads(GOOGLE_CREDS_FILE)
except json.JSONDecodeError:
    # python-dotenv may transform \n into real line breaks in quoted values.
    fixed_creds = re.sub(
        r'("private_key"\s*:\s*")(.*?)("\s*,\s*"client_email")',
        lambda m: m.group(1) + m.group(2).replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n") + m.group(3),
        GOOGLE_CREDS_FILE,
        flags=re.DOTALL,
    )
    creds_data = json.loads(fixed_creds)

if isinstance(creds_data, str):
  creds_data = json.loads(creds_data)

private_key = creds_data.get("private_key", "").strip()
if "\\n" in private_key:
    private_key = private_key.replace("\\n", "\n")
if private_key == "-----BEGIN PRIVATE KEY-----\n-----END PRIVATE KEY-----":
    raise RuntimeError("El bloque de la clave privada estÃ¡ vacÃ­o. Vuelve a descargarlo de Google Cloud.")
creds_data["private_key"] = private_key

creds = Credentials.from_service_account_info(creds_data, scopes=scope)
client = gspread.authorize(creds)
print("âœ… ConexiÃ³n exitosa con Google Sheets")

SHEET_NAME = "ventas"

EXCLUDED_WORKSHEETS = {"MALECON", "MALECON 2", "VILLAFONTANA", "RANKING_SEMANAL"}


def _sheet_key(name):
    return str(name).strip().upper()


def _is_excluded_sheet(name):
    return _sheet_key(name) in EXCLUDED_WORKSHEETS

# ==================== CACHÃ‰S GLOBALES ====================
cache_sheets = {"data": None, "timestamp": 0}
cache_global = {"data": None, "timestamp": 0}
cache_comparativa = {"data": None, "timestamp": 0}
CACHE_TTL = 300

def get_spreadsheet_data():
    """Obtiene datos del spreadsheet con cachÃ© mejorado"""
    global cache_sheets
    now = time.time()
    
    if cache_sheets["data"] and (now - cache_sheets["timestamp"]) < CACHE_TTL:
        print("âœ… Usando datos en cachÃ© (sheets)")
        return cache_sheets["data"]
    
    print("ðŸ“¡ Leyendo Google Sheets...")
    try:
        spreadsheet = client.open(SHEET_NAME)
        hojas = [ws for ws in spreadsheet.worksheets() if not _is_excluded_sheet(ws.title)]
        data = {}
        
        print(f"ðŸ” Hojas encontradas: {[hoja.title for hoja in hojas]}")
        
        # âœ… CORREGIDO: Leer TODAS las hojas, sin filtrar
        for hoja in hojas:
            try:
                print(f"ðŸ“– Leyendo: '{hoja.title}'")
                filas = hoja.get_all_values()
                data[hoja.title] = filas
                print(f"âœ… '{hoja.title}': {len(filas)} filas")
            except Exception as e:
                print(f"âŒ Error en '{hoja.title}': {e}")
                data[hoja.title] = []
        
        cache_sheets["data"] = data
        cache_sheets["timestamp"] = now
        return data
        
    except Exception as e:
        print(f"âŒ Error general: {e}")
        return cache_sheets["data"] or {}

# ==================== COLUMNAS ====================
COLUMNAS_COMPLETAS = [
    'APERTURA',
    'TOTAL VENTA C/IVA',
    'EFECTIVO',
    'T.C.',
    'UBER',
    'PEDIDOS UBER',
    'DIDI TC',
    'PEDIDOS DIDI',
    'RAPPI TC',
    'PEDIDOS RAPPI',
    'TOTAL APPS',
    'TOTAL SUCURSAL',
    'VENTA COMEDOR',
    'CUENTAS COMEDOR',
    'VENTA DOMICILIO',
    'CUENTAS DOMICILIO',
    'VENTA RAPIDO',
    'CUENTAS RAPIDO',
    'TICKET PROMEDIO'
]

ORDEN_MESES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

# ==================== HELPERS ====================
def _norm(s: str) -> str:
    """Normaliza encabezados/strings para comparaciones robustas (mayÃºsculas, sin acentos, espacios limpitos)."""
    if s is None:
        return ""
    s = str(s)
    # Primero quitar acentos
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    # Luego limpiar espacios y caracteres especiales
    s = s.replace("\u00A0", " ")  # NBSP
    s = " ".join(s.strip().split())
    # Convertir a mayÃºsculas y quitar caracteres problemÃ¡ticos
    s = s.upper()
    s = s.replace("Ã", "A").replace("Ã‰", "E").replace("Ã", "I").replace("Ã“", "O").replace("Ãš", "U")
    s = s.replace("Ã‘", "N")
    return s

def num(val):
    try:
        return float(str(val).replace(",", "").replace("$", "").strip())
    except:
        return 0.0

def num_int(val):
    try:
        return int(float(str(val).replace(",", "").replace("$", "").strip()))
    except:
        return 0

def parse_fecha(fecha_str):
    if not fecha_str:
        return None
    fecha_str = str(fecha_str).split(" ")[0]
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(fecha_str.strip(), fmt).date()
        except ValueError:
            continue
    return None

def normalizar_nombre_sucursal(nombre: str) -> str:
    """Normaliza nombres de sucursales para comparaciones flexibles"""
    if not nombre:
        return ""
    
    nombre = str(nombre).upper()
    
    # Quitar acentos
    nombre = "".join(c for c in unicodedata.normalize("NFD", nombre) if unicodedata.category(c) != "Mn")
    
    # Reemplazos comunes
    reemplazos = {
        "Ã": "A", "Ã‰": "E", "Ã": "I", "Ã“": "O", "Ãš": "U", "Ã‘": "N",
        "ZONA RIO": "ZONA RIO",
        "DARUMITA LIBERTAD": "DARUMITA LIBERTAD", 
        "DARUMITALIBERTAD": "DARUMITA LIBERTAD",
        "MALECON 2": "MALECON 2",
        "MALECON2": "MALECON 2"
    }
    
    for original, reemplazo in reemplazos.items():
        nombre = nombre.replace(original, reemplazo)
    
    # Limpiar espacios extra
    nombre = " ".join(nombre.strip().split())
    
    return nombre

# ==================== RUTAS DE AUTENTICACIÃ“N ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # DEBUG TEMPORAL
        print(f"ðŸ” USUARIO INGRESADO: '{username}'")
        print(f"ðŸ” CONTRASEÃ‘A INGRESADA: '{password}'")
        
        if username in USUARIOS:
            print(f"ðŸ” CONTRASEÃ‘A ESPERADA: '{USUARIOS[username]['password']}'")
            print(f"ðŸ” Â¿COINCIDEN?: {USUARIOS[username]['password'] == password}")
        
        if username in USUARIOS and USUARIOS[username]['password'] == password:
            user = User(username, USUARIOS[username]['nombre'], USUARIOS[username]['rol'])
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('âŒ Usuario o contraseÃ±a incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('âœ… SesiÃ³n cerrada correctamente', 'success')
    return redirect(url_for('login'))

@app.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html', usuario=current_user)

@app.route('/planeacion')
def planeacion():
    return render_template('planeacion.html')

# ==================== RUTA HOME PRINCIPAL ====================
@app.route("/")
@app.route("/home")
@login_required
def home():
    # ðŸ”’ Gerentes SIEMPRE a la grÃ¡fica
    if current_user.id == 'Gerentes':
        return redirect(url_for('reporte_grafica'))

    return render_template("home.html")

# ==================== SUPERVISION ====================
@app.route("/supervision")
@login_required
def supervision():
    return render_template("supervision.html")


@app.route("/supervision/hoja-visita", methods=["GET", "POST"])
@login_required
def supervision_hoja_visita():
    error = None
    supervisor = ""
    sucursal = ""

    if request.method == "POST":
        supervisor = (request.form.get("supervisor") or "").strip()
        password = (request.form.get("password") or "").strip()
        sucursal = (request.form.get("sucursal") or "").strip()
        foto_supervisor = request.files.get("foto_supervisor")
        foto_sucursal = request.files.get("foto_sucursal")

        usuarios_validos = {u["value"] for u in SUPERVISION_USUARIOS}
        if supervisor not in usuarios_validos:
            error = "Selecciona un supervisor válido."
        elif password.lower() != _contrasena_supervision(supervisor).lower():
            error = f"Contraseña incorrecta. Ejemplo: {_contrasena_supervision('supervisor1')}"
        elif sucursal not in SUPERVISION_SUCURSALES:
            error = "Selecciona una sucursal válida."
        elif not foto_supervisor or not foto_supervisor.filename:
            error = "Debes subir la foto del supervisor con uniforme."
        elif not foto_sucursal or not foto_sucursal.filename:
            error = "Debes subir la foto de la sucursal."
        else:
            foto_supervisor_path = _guardar_foto_supervision(
                foto_supervisor,
                SUPERVISION_UPLOAD_SUPERVISOR_DIR,
                f"uniforme_{supervisor}",
            )
            foto_sucursal_path = _guardar_foto_supervision(
                foto_sucursal,
                SUPERVISION_UPLOAD_SUCURSAL_DIR,
                f"sucursal_{_normalizar_texto_password(sucursal)}",
            )

            if not foto_supervisor_path or not foto_sucursal_path:
                error = "Formato de foto no válido. Usa JPG, JPEG, PNG o WEBP."
            else:
                ingreso_at = datetime.now(TZ_TIJUANA)
                ingreso_id = _registrar_ingreso_supervision(
                    ingreso_at=ingreso_at,
                    dashboard_user=current_user.id,
                    supervisor=supervisor,
                    sucursal=sucursal,
                    foto_supervisor=foto_supervisor_path,
                    foto_sucursal=foto_sucursal_path,
                )

                session["supervision_hoja_visita_ingreso"] = {
                    "id": ingreso_id,
                    "supervisor": supervisor,
                    "sucursal": sucursal,
                    "ingreso_at": ingreso_at.isoformat(),
                }
                return redirect(url_for("supervision_hoja_visita_home"))

    return render_template(
        "supervision_hoja_visita.html",
        supervisores=SUPERVISION_USUARIOS,
        sucursales=SUPERVISION_SUCURSALES,
        error=error,
        supervisor_seleccionado=supervisor,
        sucursal_seleccionada=sucursal,
    )


@app.route("/supervision/hoja-visita/home")
@app.route("/supervision/hoja-visita/panel/")
@login_required
def supervision_hoja_visita_home():
    ingreso = session.get("supervision_hoja_visita_ingreso")
    if not ingreso:
        flash("Primero debes identificarte para entrar a Hoja de Visita.", "error")
        return redirect(url_for("supervision_hoja_visita"))

    return render_template(
        "supervision_hoja_visita_home.html",
        ingreso=ingreso,
    )


@app.route("/supervision/sucursales")
@login_required
def supervision_sucursales():
    estadisticas = _obtener_estadisticas_supervision()
    return render_template(
        "supervision_sucursales.html",
        estadisticas=estadisticas,
    )


@app.route("/supervision/estadisticas")
@login_required
def supervision_estadisticas():
    return jsonify(_obtener_estadisticas_supervision())


@app.route("/supervision/general")
@login_required
def supervision_general():
    ingreso = session.get("supervision_hoja_visita_ingreso", {})
    panel_stats = _obtener_panel_hoja_visita(ingreso.get("supervisor", ""))
    return render_template(
        "supervision_general.html",
        ingreso=ingreso,
        panel_stats=panel_stats,
    )

# ==================== TABLA ====================
@app.route("/tabla", methods=["GET", "POST"])
@login_required
def tabla_completa():
    spreadsheet = client.open(SHEET_NAME)
    sucursales = [ws.title for ws in spreadsheet.worksheets() if not _is_excluded_sheet(ws.title)]
    sheets_data = get_spreadsheet_data()

    if not sucursales:
        return "No hay hojas disponibles para mostrar.", 400

    sucursal_seleccionada = request.form.get("sucursal") or sucursales[0]
    fecha_inicio_str = request.form.get("fecha_inicio")
    fecha_fin_str = request.form.get("fecha_fin")

    fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date() if fecha_inicio_str else None
    fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date() if fecha_fin_str else None

    all_rows = sheets_data.get(sucursal_seleccionada, [])
    if not all_rows:
        return render_template("tabla.html",
                               sucursales=sucursales,
                               sucursal_actual=sucursal_seleccionada,
                               data=[],
                               totales={},
                               fecha_inicio=fecha_inicio_str,
                               fecha_fin=fecha_fin_str)

    headers = [_norm(h) for h in all_rows[0]]
    columnas_upper = [_norm(c) for c in COLUMNAS_COMPLETAS]

    idx_map = {}
    headers_finales = []
    for col in columnas_upper:
        if col in headers:
            idx = headers.index(col)
            idx_map[col] = idx
            headers_finales.append(col)

    data = []
    for row in all_rows[1:]:
        fila = {headers_finales[j]: (row[idx_map[headers_finales[j]]].strip()
                                     if idx_map[headers_finales[j]] < len(row) else "")
                for j in range(len(headers_finales))}
        fecha_row = parse_fecha(fila.get('APERTURA', ''))
        if not fecha_row:
            continue
        if fecha_inicio and fecha_fin:
            if fecha_inicio <= fecha_row <= fecha_fin:
                data.append(fila)
        else:
            data.append(fila)

    columnas_a_sumar = [c for c in columnas_upper if c != 'APERTURA' and c in headers_finales]
    totales = {col: 0.0 for col in columnas_a_sumar}
    for fila in data:
        for col in columnas_a_sumar:
            totales[col] += num(fila.get(col, 0))

    data = sorted(data, key=lambda x: parse_fecha(x['APERTURA']) or datetime.min.date())

    def _restaurar_key(k_norm):
        for k in COLUMNAS_COMPLETAS:
            if _norm(k) == k_norm:
                return k
        return k_norm

    data_amigable = []
    for fila in data:
        data_amigable.append({_restaurar_key(k): v for k, v in fila.items()})

    totales_amigable = {_restaurar_key(k): v for k, v in totales.items()}

    return render_template("tabla.html",
                           sucursales=sucursales,
                           sucursal_actual=sucursal_seleccionada,
                           data=data_amigable,
                           totales=totales_amigable,
                           fecha_inicio=fecha_inicio_str,
                           fecha_fin=fecha_fin_str)

# ==================== RESUMEN MENSUAL ====================
@app.route("/resumen", methods=["GET", "POST"])
@login_required
def resumen_mensual():
    sheets_data = get_spreadsheet_data()
    sucursales = list(sheets_data.keys()) if sheets_data else []
    if not sucursales:
        return "No hay hojas disponibles para mostrar.", 400

    sucursal_seleccionada = request.form.get("sucursal") or sucursales[0]
    year_seleccionado = request.form.get("year") or "Todos"

    # T(19) ... AM(38): estructura fija del resumen mensual
    resumen_start_idx = 19
    resumen_end_idx = 38
    columnas_resumen = [
        "G.ANO", "G.MES", "G.TOTAL VENTA C/IVA", "G.EFECTIVO", "G.T.C.", "G.UBER", "G.PEDIDOS UBER",
        "G.DIDI TC", "G.PEDIDOS DIDI", "G.RAPPI TC", "G.PEDIDOS RAPPI", "G.TOTAL APPS",
        "G.TOTAL SUCURSAL", "G.VENTA COMEDOR", "G.CUENTAS COMEDOR", "G.VENTA DOMICILIO",
        "G.CUENTAS DOMICILIO", "G.VENTA RAPIDO", "G.CUENTAS RAPIDO", "G.TICKET PROMEDIO",
    ]
    expected_norm = [_norm(c) for c in columnas_resumen]
    year_key = _norm("G.ANO")
    mes_key = _norm("G.MES")
    total_sucursal_key = _norm("G.TOTAL SUCURSAL")
    columnas_cadena = columnas_resumen[2:]
    columnas_cadena_norm = [_norm(c) for c in columnas_cadena]
    columnas_cantidad_keys = {
        _norm("G.PEDIDOS UBER"),
        _norm("G.PEDIDOS DIDI"),
        _norm("G.PEDIDOS RAPPI"),
        _norm("G.CUENTAS COMEDOR"),
        _norm("G.CUENTAS DOMICILIO"),
        _norm("G.CUENTAS RAPIDO"),
    }
    columnas_monetarias_keys = [k for k in columnas_cadena_norm if k not in columnas_cantidad_keys]
    hoy = datetime.now().date()
    mes_actual_idx = hoy.month - 1

    def _mes_permitido(year_valor, mes_valor):
        if mes_valor not in ORDEN_MESES:
            return False
        if not year_valor or not year_valor.isdigit():
            return True
        if int(year_valor) != hoy.year:
            return True
        return ORDEN_MESES.index(mes_valor) <= mes_actual_idx

    def _extraer_estructura_resumen(rows):
        if not rows or len(rows[0]) <= resumen_end_idx:
            return None

        headers_slice = rows[0][resumen_start_idx:resumen_end_idx + 1]
        headers_norm = [_norm(h) for h in headers_slice]
        if headers_norm != expected_norm:
            return None

        indices_local = list(range(resumen_start_idx, resumen_end_idx + 1))
        year_idx = resumen_start_idx
        mes_idx = resumen_start_idx + 1
        headers_finales_local = expected_norm.copy()
        return rows, mes_idx, year_idx, indices_local, headers_finales_local

    def _calcular_totales_cadena_resumen():
        acumulado_por_mes = {mes: {col_key: 0.0 for col_key in columnas_cadena_norm} for mes in ORDEN_MESES}

        for sucursal in sucursales:
            estructura_local = _extraer_estructura_resumen(sheets_data.get(sucursal, []))
            if not estructura_local:
                continue

            rows_local, mes_idx_local, year_idx_local, indices_local, headers_local = estructura_local
            if any(col_key not in headers_local for col_key in columnas_cadena_norm):
                continue

            idxs_columnas_local = {
                col_key: indices_local[headers_local.index(col_key)]
                for col_key in columnas_cadena_norm
            }

            for row in rows_local[1:]:
                if len(row) <= resumen_end_idx:
                    continue

                year_valor_local = row[year_idx_local].strip() if year_idx_local < len(row) else ""
                mes_valor_local = row[mes_idx_local].strip().upper() if mes_idx_local < len(row) else ""

                if not year_valor_local or mes_valor_local not in ORDEN_MESES:
                    continue
                if not _mes_permitido(year_valor_local, mes_valor_local):
                    continue

                if year_seleccionado != "Todos" and year_valor_local != year_seleccionado:
                    continue

                for col_key, idx_col in idxs_columnas_local.items():
                    valor_col = num(row[idx_col]) if idx_col < len(row) else 0
                    acumulado_por_mes[mes_valor_local][col_key] += valor_col

        salida = []
        for mes in ORDEN_MESES:
            fila = {"mes": mes}
            for col_key in columnas_cadena_norm:
                fila[col_key] = round(acumulado_por_mes[mes].get(col_key, 0.0), 2)
            salida.append(fila)

        totales_finales = {
            col_key: round(sum(fila.get(col_key, 0.0) for fila in salida), 2)
            for col_key in columnas_cadena_norm
        }
        cadena_total_final = round(totales_finales.get(total_sucursal_key, 0.0), 2)
        return salida, totales_finales, cadena_total_final

    estructura = _extraer_estructura_resumen(sheets_data.get(sucursal_seleccionada, []))

    if not estructura:
        for sucursal in sucursales:
            estructura = _extraer_estructura_resumen(sheets_data.get(sucursal, []))
            if estructura:
                sucursal_seleccionada = sucursal
                break

    if not estructura:
        return render_template(
            "resumen.html",
            sucursales=sucursales,
            sucursal_actual=sucursal_seleccionada,
            years=[],
            year_actual=year_seleccionado,
            data=[],
            datos_graficos=preparar_datos_para_graficos([], year_seleccionado),
            cadena_totales_resumen=[],
            cadena_columnas=[{"label": c, "key": _norm(c)} for c in columnas_cadena],
            cadena_columnas_cantidad=list(columnas_cantidad_keys),
            cadena_columnas_monetarias=columnas_monetarias_keys,
            cadena_totales_finales={},
            total_sucursal_key=total_sucursal_key,
            cadena_total_final=0,
            error="Ninguna hoja tiene estructura valida en columnas T:AM (G.ANO ... G.TICKET PROMEDIO).",
        )

    all_rows, mes_index, year_index, indices, headers_finales = estructura
    years_disponibles = set()
    data = []

    for row in all_rows[1:]:
        if len(row) <= resumen_end_idx:
            continue

        year_valor = row[year_index].strip() if year_index < len(row) else ""
        mes_valor = row[mes_index].strip().upper() if mes_index < len(row) else ""

        if not year_valor or mes_valor not in ORDEN_MESES:
            continue
        if not _mes_permitido(year_valor, mes_valor):
            continue

        if year_valor.isdigit():
            years_disponibles.add(year_valor)

        if year_seleccionado != "Todos" and year_valor != year_seleccionado:
            continue

        fila = {}
        for j, idx in enumerate(indices):
            fila[headers_finales[j]] = row[idx] if idx < len(row) else ""

        if any(value for key, value in fila.items() if key not in [year_key, mes_key]):
            data.append(fila)

    years_disponibles = sorted(years_disponibles, key=int, reverse=True)
    data = sorted(data, key=lambda x: (
        int(x.get(year_key, 0)),
        ORDEN_MESES.index(x[mes_key].upper()) if x.get(mes_key) in ORDEN_MESES else 99
    ))

    datos_graficos = preparar_datos_para_graficos(data, year_seleccionado)
    cadena_totales_resumen, cadena_totales_finales, cadena_total_final = _calcular_totales_cadena_resumen()

    return render_template(
        "resumen.html",
        sucursales=sucursales,
        sucursal_actual=sucursal_seleccionada,
        years=years_disponibles,
        year_actual=year_seleccionado,
        data=data,
        datos_graficos=datos_graficos,
        cadena_totales_resumen=cadena_totales_resumen,
        cadena_columnas=[{"label": c, "key": _norm(c)} for c in columnas_cadena],
        cadena_columnas_cantidad=list(columnas_cantidad_keys),
        cadena_columnas_monetarias=columnas_monetarias_keys,
        cadena_totales_finales=cadena_totales_finales,
        total_sucursal_key=total_sucursal_key,
        cadena_total_final=cadena_total_final,
    )


def preparar_datos_para_graficos(data, year_seleccionado):
    """Prepara datos para graficos filtrando por anio y organizando por mes"""

    datos_agrupados = {}
    year_key = _norm("G.ANO")
    mes_key = _norm("G.MES")

    for fila in data:
        anio = fila.get(year_key, "")
        mes = fila.get(mes_key, "")

        if not anio or not mes:
            continue

        if anio not in datos_agrupados:
            datos_agrupados[anio] = {}

        try:
            venta = float(fila.get(_norm("G.TOTAL VENTA C/IVA"), 0) or 0)
            efectivo = float(fila.get(_norm("G.EFECTIVO"), 0) or 0)
            tarjeta = float(fila.get(_norm("G.T.C."), 0) or 0)
            apps = float(fila.get(_norm("G.TOTAL APPS"), 0) or 0)
            uber = float(fila.get(_norm("G.UBER"), 0) or 0)
            didi = float(fila.get(_norm("G.DIDI TC"), 0) or 0)
            rappi = float(fila.get(_norm("G.RAPPI TC"), 0) or 0)
        except (ValueError, TypeError):
            continue

        datos_agrupados[anio][mes] = {
            'venta': venta,
            'efectivo': efectivo,
            'tarjeta': tarjeta,
            'apps': apps,
            'uber': uber,
            'didi': didi,
            'rappi': rappi,
        }

    resultado = {
        'labels': [],
        'ventas_totales': [],
        'efectivo': [],
        'tarjeta': [],
        'apps_totales': [],
        'por_aÃ±o': {},
    }

    if year_seleccionado == "Todos":
        todos_meses = set()
        for anio, meses_data in datos_agrupados.items():
            todos_meses.update(meses_data.keys())

        meses_ordenados = sorted(
            todos_meses,
            key=lambda m: ORDEN_MESES.index(m) if m in ORDEN_MESES else 99,
        )

        for mes in meses_ordenados:
            venta_total = 0
            efectivo_total = 0
            tarjeta_total = 0
            apps_total = 0

            for anio, meses_data in datos_agrupados.items():
                if mes in meses_data:
                    venta_total += meses_data[mes]['venta']
                    efectivo_total += meses_data[mes]['efectivo']
                    tarjeta_total += meses_data[mes]['tarjeta']
                    apps_total += meses_data[mes]['apps']

            resultado['labels'].append(f"{mes}")
            resultado['ventas_totales'].append(venta_total)
            resultado['efectivo'].append(efectivo_total)
            resultado['tarjeta'].append(tarjeta_total)
            resultado['apps_totales'].append(apps_total)

        for anio in sorted(datos_agrupados.keys(), key=int):
            resultado['por_aÃ±o'][anio] = {
                'labels': [],
                'ventas': [],
                'efectivo': [],
                'tarjeta': [],
                'apps': [],
            }

            for mes in ORDEN_MESES:
                if mes in datos_agrupados[anio]:
                    resultado['por_aÃ±o'][anio]['labels'].append(mes)
                    resultado['por_aÃ±o'][anio]['ventas'].append(datos_agrupados[anio][mes]['venta'])
                    resultado['por_aÃ±o'][anio]['efectivo'].append(datos_agrupados[anio][mes]['efectivo'])
                    resultado['por_aÃ±o'][anio]['tarjeta'].append(datos_agrupados[anio][mes]['tarjeta'])
                    resultado['por_aÃ±o'][anio]['apps'].append(datos_agrupados[anio][mes]['apps'])
    else:
        if year_seleccionado in datos_agrupados:
            anio_data = datos_agrupados[year_seleccionado]

            for mes in ORDEN_MESES:
                if mes in anio_data:
                    resultado['labels'].append(mes)
                    resultado['ventas_totales'].append(anio_data[mes]['venta'])
                    resultado['efectivo'].append(anio_data[mes]['efectivo'])
                    resultado['tarjeta'].append(anio_data[mes]['tarjeta'])
                    resultado['apps_totales'].append(anio_data[mes]['apps'])

    return resultado

# ==================== COMPARATIVA ENTRE SUCURSALES ====================
@app.route("/comparativa", methods=["GET", "POST"])
@login_required
def comparativa():
    try:
        sheets_data = get_spreadsheet_data()
        sucursales = list(sheets_data.keys()) if sheets_data else []
        
        if not sucursales:
            return render_template("comparativa.html", 
                                 sucursales=[],
                                 sucursales_seleccionadas=[],
                                 datos_comparativa=[],
                                 error="No se pudieron cargar los datos")
        
        sucursales_seleccionadas = request.form.getlist("sucursales") 
        fecha_inicio_str = request.form.get("fecha_inicio")
        fecha_fin_str = request.form.get("fecha_fin")
        
        fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date() if fecha_inicio_str else None
        fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date() if fecha_fin_str else None
        
        if len(sucursales_seleccionadas) > 6:
            sucursales_seleccionadas = sucursales_seleccionadas[:6]
        
        if not sucursales_seleccionadas:
            sucursales_seleccionadas = sucursales[:3]
        
        datos_comparativa = []
        for sucursal in sucursales_seleccionadas:
            if sucursal in sheets_data:
                data_rows = sheets_data[sucursal]
                
                if len(data_rows) > 1:
                    headers = [_norm(h) for h in data_rows[0]]
                    data_records = []
                    fechas = []
                    totales_por_dia = []
                    
                    for row in data_rows[1:]:
                        if len(row) >= len(headers):
                            record = {headers[i]: row[i] for i in range(len(headers))}
                            
                            fecha_str = record.get('APERTURA', '')
                            fecha_row = parse_fecha(fecha_str)
                            
                            if fecha_row:
                                if fecha_inicio and fecha_fin:
                                    if fecha_inicio <= fecha_row <= fecha_fin:
                                        data_records.append(record)
                                        fechas.append(fecha_row.strftime("%Y-%m-%d"))
                                        total_dia = num(record.get('TOTAL SUCURSAL', 0))
                                        totales_por_dia.append(total_dia)
                                else:
                                    data_records.append(record)
                                    fechas.append(fecha_row.strftime("%Y-%m-%d"))
                                    total_dia = num(record.get('TOTAL SUCURSAL', 0))
                                    totales_por_dia.append(total_dia)
                    
                    total_sucursal = sum(num(fila.get('TOTAL SUCURSAL', 0)) for fila in data_records)
                    total_efectivo = sum(num(fila.get('EFECTIVO', 0)) for fila in data_records)
                    total_tc = sum(num(fila.get('T.C.', 0)) for fila in data_records)
                    total_apps = sum(num(fila.get('TOTAL APPS', 0)) for fila in data_records)
                    
                    uber = sum(num(fila.get('UBER', 0)) for fila in data_records)
                    didi = sum(num(fila.get('DIDI TC', 0)) for fila in data_records)
                    rappi = sum(num(fila.get('RAPPI TC', 0)) for fila in data_records)
                    comedor = sum(num(fila.get('VENTA COMEDOR', 0)) for fila in data_records)
                    domicilio = sum(num(fila.get('VENTA DOMICILIO', 0)) for fila in data_records)
                    rapido = sum(num(fila.get('VENTA RAPIDO', 0)) for fila in data_records)
                    
                    total_cuentas = sum(num_int(fila.get('CUENTAS COMEDOR', 0)) + 
                                      num_int(fila.get('CUENTAS DOMICILIO', 0)) + 
                                      num_int(fila.get('CUENTAS RAPIDO', 0)) for fila in data_records)
                    
                    if total_cuentas > 0:
                        ticket_promedio = round(total_sucursal / total_cuentas, 2)
                    else:
                        ticket_promedio = 0
                    
                    datos_comparativa.append({
                        'sucursal': sucursal,
                        'total_sucursal': total_sucursal,
                        'total_efectivo': total_efectivo,
                        'total_tc': total_tc,
                        'total_apps': total_apps,
                        'ticket_promedio': ticket_promedio,
                        'uber': uber,
                        'didi': didi,
                        'rappi': rappi,
                        'comedor': comedor,
                        'domicilio': domicilio,
                        'rapido': rapido,
                        'fechas': fechas,
                        'totales_por_dia': totales_por_dia
                    })
        
        return render_template("comparativa.html", 
                             sucursales=sucursales,
                             sucursales_seleccionadas=sucursales_seleccionadas,
                             datos_comparativa=datos_comparativa,
                             fecha_inicio=fecha_inicio_str,
                             fecha_fin=fecha_fin_str)
                             
    except Exception as e:
        print(f"âŒ Error en comparativa: {e}")
        return render_template("comparativa.html", 
                             sucursales=[],
                             sucursales_seleccionadas=[],
                             datos_comparativa=[],
                             error=f"Error: {str(e)}")

# ==================== DATOS PARA GRÃFICAS ====================
@app.route("/datos_grafica/<sucursal>")
@login_required
def datos_grafica(sucursal):
    """API de graficas para resumen mensual usando columnas fijas T:AM."""

    if _is_excluded_sheet(sucursal):
        return jsonify({'error': f"Sucursal no permitida: {sucursal}"}), 400

    year_seleccionado = request.args.get('year', 'Todos')
    hoy = datetime.now().date()
    mes_actual_idx = hoy.month - 1
    sheets_data = get_spreadsheet_data()
    all_rows = sheets_data.get(sucursal, []) if sheets_data else []
    if not all_rows:
        return jsonify({'error': 'Hoja vacia'}), 400

    # T(19) ... AM(38)
    start_idx = 19
    end_idx = 38
    if len(all_rows[0]) <= end_idx:
        return jsonify({'error': 'La hoja no contiene columnas T:AM'}), 400

    expected_headers = [
        "G.ANO", "G.MES", "G.TOTAL VENTA C/IVA", "G.EFECTIVO", "G.T.C.", "G.UBER", "G.PEDIDOS UBER",
        "G.DIDI TC", "G.PEDIDOS DIDI", "G.RAPPI TC", "G.PEDIDOS RAPPI", "G.TOTAL APPS",
        "G.TOTAL SUCURSAL", "G.VENTA COMEDOR", "G.CUENTAS COMEDOR", "G.VENTA DOMICILIO",
        "G.CUENTAS DOMICILIO", "G.VENTA RAPIDO", "G.CUENTAS RAPIDO", "G.TICKET PROMEDIO",
    ]
    headers_norm = [_norm(h) for h in all_rows[0][start_idx:end_idx + 1]]
    expected_norm = [_norm(h) for h in expected_headers]
    if headers_norm != expected_norm:
        return jsonify({'error': 'Encabezados invalidos en T:AM'}), 400

    year_idx = start_idx
    mes_idx = start_idx + 1
    uber_idx = start_idx + 5
    pedidos_uber_idx = start_idx + 6
    didi_idx = start_idx + 7
    pedidos_didi_idx = start_idx + 8
    rappi_idx = start_idx + 9
    pedidos_rappi_idx = start_idx + 10
    comedor_idx = start_idx + 13
    cuentas_comedor_idx = start_idx + 14
    domicilio_idx = start_idx + 15
    cuentas_domicilio_idx = start_idx + 16
    rapido_idx = start_idx + 17
    cuentas_rapido_idx = start_idx + 18

    def to_float(val, default=0):
        try:
            if isinstance(val, str):
                val = val.replace('$', '').replace(',', '').strip()
            return float(val) if val else default
        except Exception:
            return default

    def to_int(val, default=0):
        try:
            return int(to_float(val, default))
        except Exception:
            return default

    def year_match(y):
        if year_seleccionado == "Todos":
            return True
        return y == year_seleccionado

    def month_allowed(y, m):
        if m not in ORDEN_MESES:
            return False
        if not y or not y.isdigit():
            return True
        if int(y) != hoy.year:
            return True
        return ORDEN_MESES.index(m) <= mes_actual_idx

    meses = []
    for row in all_rows[1:]:
        if len(row) <= end_idx:
            continue
        year_valor = row[year_idx].strip()
        mes_valor = row[mes_idx].strip().upper()
        if not year_match(year_valor) or mes_valor not in ORDEN_MESES:
            continue
        if not month_allowed(year_valor, mes_valor):
            continue
        if mes_valor not in meses:
            meses.append(mes_valor)

    meses.sort(key=lambda m: ORDEN_MESES.index(m) if m in ORDEN_MESES else 99)
    if not meses:
        meses = ORDEN_MESES.copy()

    respuesta = {
        'meses': meses,
        'uber': [0] * len(meses),
        'didi': [0] * len(meses),
        'rappi': [0] * len(meses),
        'comedor': [0] * len(meses),
        'domicilio': [0] * len(meses),
        'rapido': [0] * len(meses),
        'pedidos_uber': [0] * len(meses),
        'pedidos_didi': [0] * len(meses),
        'pedidos_rappi': [0] * len(meses),
        'cuentas_comedor': [0] * len(meses),
        'cuentas_domicilio': [0] * len(meses),
        'cuentas_rapido': [0] * len(meses),
        'filtro_aplicado': year_seleccionado,
        'year_meses': year_seleccionado,
    }

    for row in all_rows[1:]:
        if len(row) <= end_idx:
            continue

        year_valor = row[year_idx].strip()
        mes_valor = row[mes_idx].strip().upper()
        if not year_match(year_valor) or mes_valor not in meses:
            continue
        if not month_allowed(year_valor, mes_valor):
            continue

        idx = meses.index(mes_valor)
        respuesta['uber'][idx] += to_float(row[uber_idx])
        respuesta['didi'][idx] += to_float(row[didi_idx])
        respuesta['rappi'][idx] += to_float(row[rappi_idx])
        respuesta['comedor'][idx] += to_float(row[comedor_idx])
        respuesta['domicilio'][idx] += to_float(row[domicilio_idx])
        respuesta['rapido'][idx] += to_float(row[rapido_idx])

        respuesta['pedidos_uber'][idx] += to_int(row[pedidos_uber_idx])
        respuesta['pedidos_didi'][idx] += to_int(row[pedidos_didi_idx])
        respuesta['pedidos_rappi'][idx] += to_int(row[pedidos_rappi_idx])
        respuesta['cuentas_comedor'][idx] += to_int(row[cuentas_comedor_idx])
        respuesta['cuentas_domicilio'][idx] += to_int(row[cuentas_domicilio_idx])
        respuesta['cuentas_rapido'][idx] += to_int(row[cuentas_rapido_idx])

    return jsonify(respuesta)

# ==================== DATOS GLOBAL ====================
@app.route("/datos_grafica_global")
@login_required
def datos_grafica_global():
    global cache_global
    now = time.time()

    if cache_global["data"] and (now - cache_global["timestamp"] < CACHE_TTL):
        print("Usando datos globales en cachÃ©")
        return jsonify(cache_global["data"])

    try:
        spreadsheet = client.open(SHEET_NAME)
        hojas = [ws for ws in spreadsheet.worksheets() if not _is_excluded_sheet(ws.title)]

        nombres_sucursales = []
        totales_sucursal = []
        ticket_promedio = []

        for hoja in hojas:
            nombre = hoja.title
            data = hoja.get_all_records()

            total = 0.0
            tickets = []

            for fila in data:
                total += num(fila.get('G.TOTAL SUCURSAL', 0))
                if fila.get('G.TICKET PROMEDIO'):
                    tickets.append(num(fila['G.TICKET PROMEDIO']))

            promedio = round(sum(tickets) / len(tickets), 2) if tickets else 0.0

            nombres_sucursales.append(nombre)
            totales_sucursal.append(total)
            ticket_promedio.append(promedio)

        response = {
            "sucursales": nombres_sucursales,
            "totales": totales_sucursal,
            "ticket_promedio": ticket_promedio
        }

        cache_global["data"] = response
        cache_global["timestamp"] = now

        return jsonify(response)
    except Exception as e:
        print("Error global:", e)
        return jsonify({"error": str(e)}), 500

# ==================== DATOS PARA GRÃFICAS FILTRADAS (UNA SUCURSAL) ====================
@app.route("/datos_grafica_filtrada", methods=["POST"])
@login_required
def datos_grafica_filtrada():
    sucursal = request.form.get("sucursal")
    fecha_inicio_str = request.form.get("fecha_inicio")
    fecha_fin_str = request.form.get("fecha_fin")
    metricas = request.form.getlist("metricas[]") or []

    fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date() if fecha_inicio_str else None
    fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date() if fecha_fin_str else None

    sheet = client.open(SHEET_NAME).worksheet(sucursal)
    all_rows = sheet.get_all_values()
    if not all_rows:
        return jsonify({"fechas": [], "series": {}})

    headers = [_norm(h) for h in all_rows[0]]

    columnas = [col for col in [_norm(c) for c in COLUMNAS_COMPLETAS] if col in headers]
    indices = {col: headers.index(col) for col in columnas if col in headers}

    fechas = []
    series = {col: [] for col in columnas}

    for row in all_rows[1:]:
        fecha_str = row[indices['APERTURA']] if 'APERTURA' in indices else ''
        fecha_row = parse_fecha(fecha_str)
        if not fecha_row:
            continue
        if fecha_inicio and fecha_fin and not (fecha_inicio <= fecha_row <= fecha_fin):
            continue

        fechas.append(fecha_row.strftime("%d/%m/%Y"))

        for col in columnas:
            valor = row[indices[col]] if col in indices and indices[col] < len(row) else 0
            series[col].append(num(valor))

    return jsonify({"fechas": fechas, "series": series})

# ==================== FAVICON ====================
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon"
    )

# ==================== MANEJO DE ERRORES ====================
@app.errorhandler(Exception)
def handle_error(e):
    if isinstance(e, HTTPException):
        return e
    app.logger.exception("Unhandled exception")
    return jsonify({"error": "Internal Server Error"}), 500

@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "Not Found", "path": request.path}), 404

# ==================== RANKING DE SUCURSALES (COMPARADOR SEMANAL) ====================
def obtener_ultima_semana():
    """Obtiene la Ãºltima semana disponible"""
    hoy = datetime.now().date()
    lunes = hoy - timedelta(days=hoy.weekday())
    return lunes.strftime("%Y-%m-%d")

def obtener_datos_ranking(semana):
    """Obtiene los datos del ranking para una semana especÃ­fica"""
    try:
        sheets_data = get_spreadsheet_data()
        sucursales = list(sheets_data.keys()) if sheets_data else []
        
        fecha_inicio = datetime.strptime(semana, "%Y-%m-%d").date()
        fecha_fin = fecha_inicio + timedelta(days=6)
        
        datos_semana = []
        for sucursal in sucursales:
            if sucursal in sheets_data:
                data_rows = sheets_data[sucursal]
                
                if len(data_rows) > 1:
                    headers = [_norm(h) for h in data_rows[0]]
                    data_records = []
                    
                    # Filtrar por semana seleccionada
                    for row in data_rows[1:]:
                        if len(row) >= len(headers):
                            record = {headers[i]: row[i] for i in range(len(headers))}
                            
                            fecha_str = record.get('APERTURA', '')
                            fecha_row = parse_fecha(fecha_str)
                            
                            if fecha_row and fecha_inicio <= fecha_row <= fecha_fin:
                                data_records.append(record)
                    
                    # Calcular totales
                    total_sucursal = sum(num(fila.get('TOTAL SUCURSAL', 0)) for fila in data_records)
                    total_ventas = sum(num(fila.get('TOTAL VENTA C/IVA', 0)) for fila in data_records)
                    total_efectivo = sum(num(fila.get('EFECTIVO', 0)) for fila in data_records)
                    total_apps = sum(num(fila.get('TOTAL APPS', 0)) for fila in data_records)
                    
                    datos_semana.append({
                        'sucursal': sucursal,
                        'total': total_sucursal,
                        'total_ventas': total_ventas,
                        'total_efectivo': total_efectivo,
                        'total_apps': total_apps,
                        'dias_con_datos': len(data_records)
                    })
        
        # Ordenar y asignar ranking
        datos_semana.sort(key=lambda x: x['total'], reverse=True)
        for i, dato in enumerate(datos_semana, 1):
            dato['ranking'] = i
            
        return datos_semana
        
    except Exception as e:
        print(f"âŒ Error en obtener_datos_ranking: {e}")
        return []

def procesar_comparacion_automatica(datos_actual, datos_anterior, semana_actual, semana_anterior):
    """Combina los datos de ambas semanas para la comparaciÃ³n"""
    datos_comparacion = []
    
    # Crear diccionarios para acceso rÃ¡pido
    dict_actual = {d['sucursal']: d for d in datos_actual}
    dict_anterior = {d['sucursal']: d for d in datos_anterior}
    
    # Combinar datos de todas las sucursales
    todas_sucursales = set(dict_actual.keys()) | set(dict_anterior.keys())
    
    for sucursal in todas_sucursales:
        dato_actual = dict_actual.get(sucursal, {'total': 0, 'ranking': 999, 'total_ventas': 0, 'total_efectivo': 0, 'total_apps': 0})
        dato_anterior = dict_anterior.get(sucursal, {'total': 0, 'ranking': 999, 'total_ventas': 0, 'total_efectivo': 0, 'total_apps': 0})
        
        total_actual = dato_actual['total']
        total_anterior = dato_anterior['total']
        diferencia = total_actual - total_anterior
        
        # Calcular porcentaje de cambio
        if total_anterior > 0:
            porcentaje_cambio = (diferencia / total_anterior) * 100
        else:
            porcentaje_cambio = 100 if total_actual > 0 else 0
        
        # Calcular cambio en ranking
        cambio_ranking = dato_anterior['ranking'] - dato_actual['ranking']
        
        datos_comparacion.append({
            'sucursal': sucursal,
            'total_actual': total_actual,
            'total_anterior': total_anterior,
            'diferencia': diferencia,
            'porcentaje_cambio': porcentaje_cambio,
            'ranking_actual': dato_actual['ranking'],
            'ranking_anterior': dato_anterior['ranking'],
            'cambio_ranking': cambio_ranking,
            'total_ventas_actual': dato_actual['total_ventas'],
            'total_efectivo_actual': dato_actual['total_efectivo'],
            'total_apps_actual': dato_actual['total_apps']
        })
    
    # Ordenar por total actual (ranking actual)
    datos_comparacion.sort(key=lambda x: x['total_actual'], reverse=True)
    
    return datos_comparacion

def obtener_fechas_semana(semana):
    """Obtiene las fechas de inicio y fin para una semana especÃ­fica"""
    try:
        fecha_inicio = datetime.strptime(semana, "%Y-%m-%d").date()
        fecha_fin = fecha_inicio + timedelta(days=6)
        return fecha_inicio.strftime("%d/%m/%Y"), fecha_fin.strftime("%d/%m/%Y")
    except:
        return ("dd/mm/yyyy", "dd/mm/yyyy")

def generar_opciones_semanas():
    """Genera opciones de semanas para el selector (Ãºltimas 12 semanas)"""
    opciones = []
    hoy = datetime.now().date()
    
    for i in range(12):
        # Calcular lunes de cada semana (empezando por la actual)
        lunes = hoy - timedelta(days=hoy.weekday() + (7 * i))
        domingo = lunes + timedelta(days=6)
        
        opciones.append({
            'value': lunes.strftime("%Y-%m-%d"),
            'label': f"Semana {lunes.strftime('%U')}: {lunes.strftime('%d/%m/%Y')} - {domingo.strftime('%d/%m/%Y')}"
        })
    
    return opciones

@app.route("/ranking", methods=["GET", "POST"])
@login_required
def ranking_sucursales():
    try:
        # Obtener la semana actual del formulario o usar la Ãºltima disponible
        semana_actual = request.form.get("semana")
        
        if not semana_actual:
            semana_actual = obtener_ultima_semana()
        
        # Calcular semana anterior automÃ¡ticamente
        try:
            fecha_actual = datetime.strptime(semana_actual, "%Y-%m-%d").date()
            fecha_anterior = fecha_actual - timedelta(days=7)
            semana_anterior = fecha_anterior.strftime("%Y-%m-%d")
        except:
            # Si hay error en el cÃ¡lculo, usar semana anterior numÃ©rica
            semana_anterior = "semana-anterior"
        
        # Obtener datos de ambas semanas
        datos_actual = obtener_datos_ranking(semana_actual)
        datos_anterior = obtener_datos_ranking(semana_anterior)
        
        # Procesar comparaciÃ³n automÃ¡tica
        datos_comparacion = procesar_comparacion_automatica(datos_actual, datos_anterior, semana_actual, semana_anterior)
        
        # Calcular totales y crecimiento
        total_general_actual = sum(d.get('total_actual', 0) for d in datos_comparacion)
        total_general_anterior = sum(d.get('total_anterior', 0) for d in datos_comparacion)
        
        if total_general_anterior > 0:
            crecimiento_total = ((total_general_actual - total_general_anterior) / total_general_anterior) * 100
        else:
            crecimiento_total = 0
        
        # Obtener opciones de semanas para el dropdown
        opciones_semanas = generar_opciones_semanas()
        
        # Obtener fechas para mostrar
        fecha_inicio_actual, fecha_fin_actual = obtener_fechas_semana(semana_actual)
        fecha_inicio_anterior, fecha_fin_anterior = obtener_fechas_semana(semana_anterior)
        
        return render_template("ranking.html", 
                             datos_comparacion=datos_comparacion,
                             semana_actual=semana_actual,
                             semana_anterior=semana_anterior,
                             total_general_actual=total_general_actual,
                             total_general_anterior=total_general_anterior,
                             crecimiento_total=crecimiento_total,
                             fecha_inicio_actual=fecha_inicio_actual,
                             fecha_fin_actual=fecha_fin_actual,
                             fecha_inicio_anterior=fecha_inicio_anterior,
                             fecha_fin_anterior=fecha_fin_anterior,
                             opciones_semanas=opciones_semanas)
                             
    except Exception as e:
        print(f"âŒ Error en ranking: {e}")
        # En caso de error, mostrar pÃ¡gina con datos vacÃ­os
        return render_template("ranking.html", 
                             datos_comparacion=[],
                             semana_actual="",
                             semana_anterior="",
                             total_general_actual=0,
                             total_general_anterior=0,
                             crecimiento_total=0,
                             fecha_inicio_actual="",
                             fecha_fin_actual="",
                             fecha_inicio_anterior="",
                             fecha_fin_anterior="",
                             opciones_semanas=[],
                             error=f"Error: {str(e)}")

# ==================== REPORTE SEMANAL SIMPLIFICADO PARA USUARIO Gerentes ====================
@app.route("/reporte-grafica")
@login_required
def reporte_grafica():
    if current_user.id != 'Gerentes':
        flash('âŒ No tienes permisos para acceder a esta pÃ¡gina', 'error')
        return redirect(url_for('home'))

    try:
        sheets_data = get_spreadsheet_data()
        sucursales = list(sheets_data.keys()) if sheets_data else []

        if not sucursales:
            return render_template(
                "reporte_grafica.html",
                datos_semana_anterior=[],
                rango_semana="No disponible",
                error="No se pudieron cargar los datos"
            )

        hoy = datetime.now().date()
        lunes_semana_actual = hoy - timedelta(days=hoy.weekday())
        lunes_semana_anterior = lunes_semana_actual - timedelta(days=7)
        domingo_semana_anterior = lunes_semana_anterior + timedelta(days=6)

        rango_semana = (
            f"{lunes_semana_anterior.strftime('%d/%m/%Y')} "
            f"al {domingo_semana_anterior.strftime('%d/%m/%Y')}"
        )

        datos_semana_anterior = []

        for sucursal in sucursales:
            data_rows = sheets_data.get(sucursal, [])
            if len(data_rows) <= 1:
                continue

            headers = [_norm(h) for h in data_rows[0]]
            data_records = []

            for row in data_rows[1:]:
                if len(row) >= len(headers):
                    record = {headers[i]: row[i] for i in range(len(headers))}
                    fecha_row = parse_fecha(record.get('APERTURA', ''))

                    if fecha_row and lunes_semana_anterior <= fecha_row <= domingo_semana_anterior:
                        data_records.append(record)

            total_semanal = sum(num(r.get('TOTAL SUCURSAL', 0)) for r in data_records)

            datos_semana_anterior.append({
                'nombre': sucursal,
                'total_semanal': total_semanal
            })

        datos_semana_anterior.sort(key=lambda x: x['total_semanal'], reverse=True)

        return render_template(
            "reporte_grafica.html",
            datos_semana_anterior=datos_semana_anterior,
            rango_semana=rango_semana
        )

    except Exception as e:
        print(f"âŒ Error en reporte grÃ¡fica: {e}")
        return render_template(
            "reporte_grafica.html",
            datos_semana_anterior=[],
            rango_semana="Error",
            error=str(e)
        )


# ==================== REPORTE SEMANAL DE PEDIDOS (TEMPLATE NUEVO) ====================
@app.route("/reporte-pedidos-semanales")
@login_required
def reporte_pedidos_semanales():
    try:
        sheets_data = get_spreadsheet_data()
        sucursales = list(sheets_data.keys()) if sheets_data else []

        # Esta vista debe incluir MATRIZ aunque este excluida globalmente en otros modulos.
        try:
            if "MATRIZ" not in sheets_data:
                ws_matriz = client.open(SHEET_NAME).worksheet("MATRIZ")
                sheets_data["MATRIZ"] = ws_matriz.get_all_values()
            if "MATRIZ" not in sucursales:
                sucursales.append("MATRIZ")
        except Exception:
            pass

        if not sucursales:
            return render_template(
                "reporte_pedidos_semanales.html",
                sucursales=[],
                rango_fechas="No disponible",
                pedidos_chart_data={"labels": [], "series": {}},
                error="No se pudieron cargar datos de sucursales."
            )

        hoy = datetime.now().date()
        anio_inicio = hoy.year if hoy.month == 12 else hoy.year - 1
        fecha_inicio = datetime(anio_inicio, 12, 1).date()
        fecha_fin = hoy

        labels = []
        cursor = fecha_inicio
        while cursor <= fecha_fin:
            fin_semana = min(cursor + timedelta(days=6), fecha_fin)
            labels.append(f"{cursor.strftime('%d/%m')} - {fin_semana.strftime('%d/%m')}")
            cursor = fin_semana + timedelta(days=1)

        series = {}
        for sucursal in sucursales:
            uber = [0.0] * len(labels)
            didi = [0.0] * len(labels)
            rows = sheets_data.get(sucursal, [])

            if rows and len(rows) > 1:
                headers_norm = [_norm(h) for h in rows[0]]

                def _idx(col_name):
                    key = _norm(col_name)
                    return headers_norm.index(key) if key in headers_norm else -1

                idx_apertura = _idx("APERTURA")
                idx_uber = _idx("PEDIDOS UBER")
                idx_didi = _idx("PEDIDOS DIDI")

                if idx_apertura >= 0:
                    for row in rows[1:]:
                        if idx_apertura >= len(row):
                            continue

                        fecha_row = parse_fecha(row[idx_apertura])
                        if not fecha_row or not (fecha_inicio <= fecha_row <= fecha_fin):
                            continue

                        idx_semana = (fecha_row - fecha_inicio).days // 7
                        if idx_semana < 0 or idx_semana >= len(labels):
                            continue

                        if 0 <= idx_uber < len(row):
                            uber[idx_semana] += num(row[idx_uber])
                        if 0 <= idx_didi < len(row):
                            didi[idx_semana] += num(row[idx_didi])

            series[sucursal] = {
                "uber": [round(v, 2) for v in uber],
                "didi": [round(v, 2) for v in didi]
            }

        return render_template(
            "reporte_pedidos_semanales.html",
            sucursales=sucursales,
            rango_fechas=f"{fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}",
            pedidos_chart_data={"labels": labels, "series": series}
        )

    except Exception as e:
        print(f"❌ Error en reporte_pedidos_semanales: {e}")
        return render_template(
            "reporte_pedidos_semanales.html",
            sucursales=[],
            rango_fechas="Error",
            pedidos_chart_data={"labels": [], "series": {}},
            error=str(e)
        )

# ==================== ACTUALIZAR ESTATUS AUTOMÃTICO ====================
@app.route("/actualizar_estatus_automatico", methods=["POST"])
@login_required
def actualizar_estatus_automatico():
    """FunciÃ³n que cambia automÃ¡ticamente el estatus de permisos prÃ³ximos a vencer"""
    
    try:
        # Conectar a Supabase
        supabase_url = 'https://uooffrtjajluvhcauctk.supabase.co'
        supabase_key = 'sb_publishable_ib_7iPl1ccS0PGo3yKzggQ_nWMi9CU8'
        
        # Usar supabase-py o requests
        import requests
        
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        # Fecha actual (hora de MÃ©xico)
        timezone_mx = pytz.timezone('America/Mexico_City')
        hoy = datetime.now(timezone_mx).date()
        fecha_limite = hoy + timedelta(days=7)
        
        # 1. BUSCAR PERMISOS QUE ESTÃN POR VENCER (7 dÃ­as o menos)
        print(f"Buscando permisos que vencen entre {hoy} y {fecha_limite}")
        
        # Obtener todos los permisos que tienen fecha_renovacion
        response = requests.get(
            f'{supabase_url}/rest/v1/datos_financieros',
            headers=headers,
            params={
                'select': 'id,sucursal,fecha_renovacion,estatus',
                'fecha_renovacion.not.is': 'null',
                'estatus.not.in': '(vencido,completado)'
            }
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'No se pudieron obtener los datos'}), 400
        
        permisos = response.json()
        cambios_realizados = 0
        
        for permiso in permisos:
            if not permiso.get('fecha_renovacion'):
                continue
            
            try:
                fecha_renovacion = datetime.strptime(permiso['fecha_renovacion'], '%Y-%m-%d').date()
                dias_faltantes = (fecha_renovacion - hoy).days
                
                # Si faltan 7 dÃ­as o menos y NO estÃ¡ ya como "proximo-a-vencer"
                if 0 <= dias_faltantes <= 7 and permiso.get('estatus') != 'proximo-a-vencer':
                    print(f"âœ“ {permiso['sucursal']}: Cambiando a 'proximo-a-vencer' (vence en {dias_faltantes} dÃ­as)")
                    
                    # Actualizar en Supabase
                    update_response = requests.patch(
                        f"{supabase_url}/rest/v1/datos_financieros?id=eq.{permiso['id']}",
                        headers=headers,
                        json={
                            'estatus': 'proximo-a-vencer',
                            'actualizado_en': datetime.now(timezone_mx).isoformat()
                        }
                    )
                    
                    if update_response.status_code in [200, 204]:
                        cambios_realizados += 1
                    else:
                        print(f"Error actualizando {permiso['sucursal']}: {update_response.text}")
                
                # Si ya venciÃ³ y NO estÃ¡ como "vencido"
                elif dias_faltantes < 0 and permiso.get('estatus') != 'vencido':
                    print(f"âœ— {permiso['sucursal']}: Cambiando a 'vencido'")
                    
                    update_response = requests.patch(
                        f"{supabase_url}/rest/v1/datos_financieros?id=eq.{permiso['id']}",
                        headers=headers,
                        json={
                            'estatus': 'vencido',
                            'actualizado_en': datetime.now(timezone_mx).isoformat()
                        }
                    )
                    
                    if update_response.status_code in [200, 204]:
                        cambios_realizados += 1
                
            except Exception as e:
                print(f"Error procesando permiso {permiso.get('id')}: {e}")
                continue
        
        print(f"âœ… {cambios_realizados} permisos actualizados")
        return jsonify({
            'success': True,
            'cambios': cambios_realizados,
            'message': f'Se actualizaron {cambios_realizados} permisos'
        })
        
    except Exception as e:
        print(f"âŒ Error general: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ACTUALIZAR ESTATUS (API PARA FRONTEND) ====================
@app.route("/api/actualizar_estatus", methods=["POST"])
@login_required
def api_actualizar_estatus():
    """API para actualizar estatus desde el frontend"""
    try:
        import requests
        from datetime import datetime, timedelta
        
        # ConfiguraciÃ³n Supabase
        SUPABASE_URL = 'https://uooffrtjajluvhcauctk.supabase.co'
        SUPABASE_KEY = 'sb_publishable_ib_7iPl1ccS0PGo3yKzggQ_nWMi9CU8'
        
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Obtener fecha actual
        hoy = datetime.now().date()
        fecha_limite = hoy + timedelta(days=7)
        
        print(f"ðŸ”„ Buscando permisos que vencen hasta {fecha_limite}")
        
        # Obtener todos los permisos con fecha de renovaciÃ³n
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/datos_financieros',
            headers=headers,
            params={
                'select': 'id,sucursal,fecha_renovacion,estatus',
                'fecha_renovacion.not.is': 'null'
            }
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'No se pudieron obtener datos'}), 400
        
        permisos = response.json()
        cambios = []
        
        for permiso in permisos:
            fecha_str = permiso.get('fecha_renovacion')
            if not fecha_str:
                continue
            
            try:
                fecha_ven = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                dias_faltantes = (fecha_ven - hoy).days
                
                nuevo_estatus = None
                
                # Si ya venciÃ³
                if fecha_ven < hoy and permiso.get('estatus') != 'vencido':
                    nuevo_estatus = 'vencido'
                
                # Si faltan 7 dÃ­as o menos
                elif 0 <= dias_faltantes <= 7 and permiso.get('estatus') != 'proximo-a-vencer':
                    nuevo_estatus = 'proximo-a-vencer'
                
                if nuevo_estatus:
                    # Actualizar en Supabase
                    update_response = requests.patch(
                        f"{SUPABASE_URL}/rest/v1/datos_financieros?id=eq.{permiso['id']}",
                        headers=headers,
                        json={
                            'estatus': nuevo_estatus,
                            'actualizado_en': datetime.now().isoformat()
                        }
                    )
                    
                    if update_response.status_code in [200, 204]:
                        cambios.append({
                            'id': permiso['id'],
                            'sucursal': permiso['sucursal'],
                            'estatus_anterior': permiso.get('estatus'),
                            'estatus_nuevo': nuevo_estatus,
                            'dias': dias_faltantes
                        })
                        
            except Exception as e:
                print(f"Error con permiso {permiso.get('id')}: {e}")
                continue
        
        print(f"âœ… {len(cambios)} permisos actualizados")
        return jsonify({
            'success': True,
            'total_cambios': len(cambios),
            'cambios': cambios,
            'fecha_actual': hoy.isoformat()
        })
        
    except Exception as e:
        print(f"âŒ Error general: {e}")
        return jsonify({'error': str(e)}), 500
        
        # ==================== RUTAS PARA REPORTES DE PERMISOS ====================
@app.route("/api/permisos")
@login_required
def obtener_permisos():
    """API para obtener todos los permisos"""
    try:
        import requests
        
        # ConfiguraciÃ³n Supabase
        SUPABASE_URL = 'https://uooffrtjajluvhcauctk.supabase.co'
        SUPABASE_KEY = 'sb_publishable_ib_7iPl1ccS0PGo3yKzggQ_nWMi9CU8'
        
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Obtener todos los permisos
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/datos_financieros',
            headers=headers,
            params={
                'select': 'id,bloque,sucursal,tipo_permiso,existencia,fecha_expedicion,fecha_renovacion,estatus',
                'order': 'sucursal.asc'
            }
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'No se pudieron obtener los permisos'}), 400
        
        permisos = response.json()
        
        # Formatear datos para el frontend
        permisos_formateados = []
        for permiso in permisos:
            permisos_formateados.append({
                'id': permiso.get('id'),
                'bloque': permiso.get('bloque', ''),
                'sucursal': permiso.get('sucursal', ''),
                'permiso': permiso.get('tipo_permiso', ''),
                'existencia': permiso.get('existencia', ''),
                'fecha_expedicion': permiso.get('fecha_expedicion', ''),
                'fecha_renovacion': permiso.get('fecha_renovacion', ''),
                'estatus': permiso.get('estatus', '')
            })
        
        return jsonify({
            'success': True,
            'permisos': permisos_formateados,
            'total': len(permisos_formateados)
        })
        
    except Exception as e:
        print(f"âŒ Error obteniendo permisos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/permisos/estadisticas")
@login_required
def obtener_estadisticas_permisos():
    """API para obtener estadÃ­sticas de permisos"""
    try:
        import requests
        
        # ConfiguraciÃ³n Supabase
        SUPABASE_URL = 'https://uooffrtjajluvhcauctk.supabase.co'
        SUPABASE_KEY = 'sb_publishable_ib_7iPl1ccS0PGo3yKzggQ_nWMi9CU8'
        
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Obtener todos los permisos para contar
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/datos_financieros',
            headers=headers,
            params={
                'select': 'estatus'
            }
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'No se pudieron obtener las estadÃ­sticas'}), 400
        
        permisos = response.json()
        
        # Contar por estatus
        contador = {
            'VIGENTE': 0,
            'VENCIDO': 0,
            'EN TRÃMITE': 0,
            'PENDIENTE': 0,
            'PRÃ“XIMO A VENCER': 0
        }
        
        for permiso in permisos:
            estatus = permiso.get('estatus', '').upper()
            if estatus in contador:
                contador[estatus] += 1
            elif 'VENCID' in estatus:
                contador['VENCIDO'] += 1
            elif 'TRÃMITE' in estatus or 'TRAMITE' in estatus:
                contador['EN TRÃMITE'] += 1
            elif 'PENDIENTE' in estatus:
                contador['PENDIENTE'] += 1
            elif 'PRÃ“XIMO' in estatus or 'PROXIMO' in estatus:
                contador['PRÃ“XIMO A VENCER'] += 1
            elif 'VIGENTE' in estatus:
                contador['VIGENTE'] += 1
        
        total = len(permisos)
        
        # Calcular porcentajes
        porcentajes = {}
        for key, value in contador.items():
            porcentajes[key] = round((value / total * 100), 2) if total > 0 else 0
        
        return jsonify({
            'success': True,
            'estadisticas': contador,
            'porcentajes': porcentajes,
            'total': total
        })
        
    except Exception as e:
        print(f"âŒ Error obteniendo estadÃ­sticas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/permisos/filtrar/<estatus>")
@login_required
def filtrar_permisos_por_estatus(estatus):
    """API para filtrar permisos por estatus"""
    try:
        import requests
        
        # ConfiguraciÃ³n Supabase
        SUPABASE_URL = 'https://uooffrtjajluvhcauctk.supabase.co'
        SUPABASE_KEY = 'sb_publishable_ib_7iPl1ccS0PGo3yKzggQ_nWMi9CU8'
        
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Mapear nombres de estatus para la consulta
        estatus_map = {
            'vigentes': 'VIGENTE',
            'vencidos': 'VENCIDO',
            'en-tramite': 'EN TRÃMITE',
            'pendientes': 'PENDIENTE',
            'proximos-a-vencer': 'PRÃ“XIMO A VENCER'
        }
        
        estatus_bd = estatus_map.get(estatus.lower(), estatus.upper())
        
        # Obtener permisos filtrados por estatus
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/datos_financieros',
            headers=headers,
            params={
                'select': 'id,bloque,sucursal,tipo_permiso,existencia,fecha_expedicion,fecha_renovacion,estatus',
                'estatus': f'eq.{estatus_bd}',
                'order': 'sucursal.asc'
            }
        )
        
        if response.status_code != 200:
            return jsonify({'error': f'No se pudieron obtener los permisos {estatus}'}), 400
        
        permisos = response.json()
        
        # Formatear datos para el frontend
        permisos_formateados = []
        for permiso in permisos:
            permisos_formateados.append({
                'id': permiso.get('id'),
                'bloque': permiso.get('bloque', ''),
                'sucursal': permiso.get('sucursal', ''),
                'permiso': permiso.get('tipo_permiso', ''),
                'existencia': permiso.get('existencia', ''),
                'fecha_expedicion': permiso.get('fecha_expedicion', ''),
                'fecha_renovacion': permiso.get('fecha_renovacion', ''),
                'estatus': permiso.get('estatus', '')
            })
        
        return jsonify({
            'success': True,
            'permisos': permisos_formateados,
            'total': len(permisos_formateados),
            'estatus': estatus_bd
        })
        
    except Exception as e:
        print(f"âŒ Error filtrando permisos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/reporte-permisos/todos")
@login_required
def generar_reporte_general():
    """Generar reporte con TODOS los permisos"""
    try:
        import requests
        from datetime import datetime
        
        # ConfiguraciÃ³n Supabase
        SUPABASE_URL = 'https://uooffrtjajluvhcauctk.supabase.co'
        SUPABASE_KEY = 'sb_publishable_ib_7iPl1ccS0PGo3yKzggQ_nWMi9CU8'
        
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Obtener TODOS los permisos
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/datos_financieros',
            headers=headers,
            params={
                'select': 'id,bloque,sucursal,tipo_permiso,existencia,fecha_expedicion,fecha_renovacion,estatus',
                'order': 'estatus.asc,sucursal.asc'
            }
        )
        
        if response.status_code != 200:
            return f"Error al obtener los permisos", 400
        
        permisos = response.json()
        
        # Contar por estatus
        contador_estatus = {}
        for permiso in permisos:
            estatus = permiso.get('estatus', 'SIN ESTATUS')
            contador_estatus[estatus] = contador_estatus.get(estatus, 0) + 1
        
        # Formatear fechas
        for permiso in permisos:
            if permiso.get('fecha_expedicion'):
                try:
                    fecha = datetime.strptime(permiso['fecha_expedicion'], '%Y-%m-%d')
                    permiso['fecha_expedicion_formatted'] = fecha.strftime('%d/%m/%Y')
                except:
                    permiso['fecha_expedicion_formatted'] = permiso['fecha_expedicion']
            
            if permiso.get('fecha_renovacion'):
                try:
                    fecha = datetime.strptime(permiso['fecha_renovacion'], '%Y-%m-%d')
                    permiso['fecha_renovacion_formatted'] = fecha.strftime('%d/%m/%Y')
                except:
                    permiso['fecha_renovacion_formatted'] = permiso['fecha_renovacion']
        
        # Generar HTML del reporte general
        fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        html = f'''
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Reporte General de Permisos - La Postal</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 2px solid #b71c1c;
                    padding-bottom: 20px;
                }}
                .header h1 {{
                    color: #b71c1c;
                    font-weight: bold;
                }}
                .stats-container {{
                    display: flex;
                    justify-content: space-around;
                    flex-wrap: wrap;
                    margin-bottom: 30px;
                    gap: 15px;
                }}
                .stat-card {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    min-width: 150px;
                    text-align: center;
                    border-left: 4px solid;
                }}
                .stat-card.vigente {{ border-color: #4caf50; }}
                .stat-card.vencido {{ border-color: #f44336; }}
                .stat-card.tramite {{ border-color: #ff9800; }}
                .stat-card.pendiente {{ border-color: #9c27b0; }}
                .stat-card.proximo {{ border-color: #ff9800; }}
                
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th {{
                    background-color: #b71c1c;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    border: 1px solid #ddd;
                }}
                td {{
                    padding: 10px;
                    border: 1px solid #ddd;
                }}
                .estatus-badge {{
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 0.85rem;
                }}
                @media print {{
                    .no-print {{ display: none; }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Reporte General de Permisos - La Postal</h1>
                <h3>Todos los permisos</h3>
                <p><strong>Fecha de generaciÃ³n:</strong> {fecha_actual}</p>
                <p><strong>Total de permisos:</strong> {len(permisos)}</p>
            </div>
            
            <div class="stats-container">
        '''
        
        # Agregar tarjetas de estadÃ­sticas
        for estatus, cantidad in contador_estatus.items():
            clase_color = 'vigente' if estatus == 'VIGENTE' else \
                         'vencido' if estatus == 'VENCIDO' else \
                         'tramite' if 'TRÃMITE' in estatus else \
                         'pendiente' if estatus == 'PENDIENTE' else \
                         'proximo' if 'PRÃ“XIMO' in estatus else ''
            
            html += f'''
                <div class="stat-card {clase_color}">
                    <div style="font-size: 1.5rem; font-weight: bold;">{cantidad}</div>
                    <div>{estatus}</div>
                </div>
            '''
        
        html += f'''
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Bloque</th>
                        <th>Sucursal</th>
                        <th>Permiso</th>
                        <th>Existencia</th>
                        <th>Fecha ExpediciÃ³n</th>
                        <th>Fecha RenovaciÃ³n</th>
                        <th>Estatus</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        # Agregar filas de datos
        for i, permiso in enumerate(permisos, 1):
            estatus_class = ""
            estatus_text = permiso.get('estatus', '')
            if estatus_text == 'VIGENTE':
                estatus_class = 'background-color: #d4edda; color: #155724;'
            elif estatus_text == 'VENCIDO':
                estatus_class = 'background-color: #f8d7da; color: #721c24;'
            elif 'TRÃMITE' in estatus_text:
                estatus_class = 'background-color: #fff3cd; color: #856404;'
            elif estatus_text == 'PENDIENTE':
                estatus_class = 'background-color: #e2e3e5; color: #383d41;'
            elif 'PRÃ“XIMO' in estatus_text:
                estatus_class = 'background-color: #ffeaa7; color: #8c7e00;'
            
            html += f'''
                    <tr>
                        <td>{i}</td>
                        <td>{permiso.get('bloque', '')}</td>
                        <td>{permiso.get('sucursal', '')}</td>
                        <td>{permiso.get('tipo_permiso', '')}</td>
                        <td>{permiso.get('existencia', '')}</td>
                        <td>{permiso.get('fecha_expedicion_formatted', '')}</td>
                        <td>{permiso.get('fecha_renovacion_formatted', '')}</td>
                        <td><span class="estatus-badge" style="{estatus_class}">{estatus_text}</span></td>
                    </tr>
            '''
        
        html += '''
                </tbody>
            </table>
            
            <div class="footer" style="margin-top: 30px; text-align: center; color: #666; font-size: 0.9rem;">
                <p>Sistema de GestiÃ³n de Permisos - La Postal</p>
            </div>
        </body>
        </html>
        '''
        
        return html
        
    except Exception as e:
        print(f"âŒ Error generando reporte general: {e}")
        return f"Error al generar el reporte: {str(e)}", 500

@app.route("/reporte-permisos/<estatus>")
@login_required
def generar_reporte_permisos(estatus):
    """Generar reporte en formato HTML como el ejemplo que muestras"""
    try:
        import requests
        from datetime import datetime
        
        # ConfiguraciÃ³n Supabase
        SUPABASE_URL = 'https://uooffrtjajluvhcauctk.supabase.co'
        SUPABASE_KEY = 'sb_publishable_ib_7iPl1ccS0PGo3yKzggQ_nWMi9CU8'
        
        print(f"ðŸ” Generando reporte para estatus: {estatus}")
        
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # DEBUG: Primero probar la conexiÃ³n sin filtros
        print("ðŸ” Probando conexiÃ³n a Supabase...")
        test_response = requests.get(
            f'{SUPABASE_URL}/rest/v1/datos_financieros',
            headers=headers,
            params={
                'select': 'count',
                'limit': 1
            }
        )
        
        print(f" ConexiÃ³n Supabase: {test_response.status_code}")
        if test_response.status_code != 200:
            print(f" Error conexiÃ³n: {test_response.text}")
        
        # Mapear nombres de estatus con diferentes formatos posibles
        estatus_map = {
            'vigentes': ['VIGENTE', 'Vigente', 'vigente'],
            'vencidos': ['VENCIDO', 'Vencido', 'vencido'],
            'en-tramite': ['EN TRÃMITE', 'En TrÃ¡mite', 'en trÃ¡mite', 'TRAMITE'],
            'pendientes': ['PENDIENTE', 'Pendiente', 'pendiente'],
            'proximos-a-vencer': ['PRÃ“XIMO A VENCER', 'PrÃ³ximo a Vencer', 'prÃ³ximo a vencer', 'PROXIMO A VENCER']
        }
        
        # Para "todos", obtener sin filtrar
        if estatus.lower() == 'todos':
            print("ðŸ” Obteniendo TODOS los permisos (sin filtro)")
            response = requests.get(
                f'{SUPABASE_URL}/rest/v1/datos_financieros',
                headers=headers,
                params={
                    'select': 'id,bloque,sucursal,tipo_permiso,existencia,fecha_expedicion,fecha_renovacion,estatus',
                    'order': 'sucursal.asc'
                }
            )
            estatus_bd = "TODOS"
        else:
            # Para filtros especÃ­ficos, probar diferentes formatos
            estatus_options = estatus_map.get(estatus.lower(), [estatus.upper()])
            print(f" Buscando estatus: {estatus_options}")
            
            # Intentar cada formato posible
            permisos = []
            for estatus_format in estatus_options:
                print(f"  Probando formato: '{estatus_format}'")
                response = requests.get(
                    f'{SUPABASE_URL}/rest/v1/datos_financieros',
                    headers=headers,
                    params={
                        'select': 'id,bloque,sucursal,tipo_permiso,existencia,fecha_expedicion,fecha_renovacion,estatus',
                        'estatus': f'eq.{estatus_format}',
                        'order': 'sucursal.asc'
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data:  # Si encontramos datos con este formato
                        print(f"   Encontrados {len(data)} permisos con formato '{estatus_format}'")
                        permisos = data
                        estatus_bd = estatus_format
                        break
                    else:
                        print(f"    0 permisos con formato '{estatus_format}'")
                else:
                    print(f"   Error con formato '{estatus_format}': {response.status_code}")
            
            # Si no encontramos con ningÃºn formato, intentar bÃºsqueda case-insensitive
            if not permisos and estatus.lower() != 'todos':
                print("ðŸ” Intentando bÃºsqueda case-insensitive...")
                response = requests.get(
                    f'{SUPABASE_URL}/rest/v1/datos_financieros',
                    headers=headers,
                    params={
                        'select': 'id,bloque,sucursal,tipo_permiso,existencia,fecha_expedicion,fecha_renovacion,estatus',
                        'order': 'sucursal.asc'
                    }
                )
                
                if response.status_code == 200:
                    all_permisos = response.json()
                    # Filtrar localmente por estatus (case-insensitive)
                    search_term = estatus.lower()
                    permisos = [
                        p for p in all_permisos 
                        if p.get('estatus') and search_term in p.get('estatus', '').lower()
                    ]
                    print(f" Encontrados {len(permisos)} permisos con bÃºsqueda case-insensitive")
                    estatus_bd = estatus.upper()
        
        if response.status_code != 200:
            error_msg = f"Error {response.status_code} al obtener los permisos: {response.text}"
            print(f" {error_msg}")
            return f"<h1>Error</h1><p>{error_msg}</p>", 400
        
        # Si estamos en el flujo "todos" o bÃºsqueda especÃ­fica
        if estatus.lower() == 'todos':
            permisos = response.json()
            print(f" Obtenidos {len(permisos)} permisos (todos)")
        elif not permisos:  # Si aÃºn no tenemos permisos
            permisos = []
            print("  No se encontraron permisos con el filtro aplicado")
        
        print(f" Total de permisos a mostrar: {len(permisos)}")
        
        # Formatear fechas para mostrar
        permisos_formateados = []
        for permiso in permisos:
            permiso_formateado = permiso.copy()
            
            # Formatear fecha expediciÃ³n
            fecha_exp = permiso.get('fecha_expedicion', '')
            if fecha_exp:
                try:
                    # Intentar diferentes formatos de fecha
                    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
                        try:
                            fecha = datetime.strptime(fecha_exp, fmt)
                            permiso_formateado['fecha_expedicion_formatted'] = fecha.strftime('%d/%m/%Y')
                            break
                        except:
                            continue
                    else:
                        permiso_formateado['fecha_expedicion_formatted'] = fecha_exp
                except:
                    permiso_formateado['fecha_expedicion_formatted'] = fecha_exp
            else:
                permiso_formateado['fecha_expedicion_formatted'] = 'N/A'
            
            # Formatear fecha renovaciÃ³n
            fecha_ren = permiso.get('fecha_renovacion', '')
            if fecha_ren:
                try:
                    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
                        try:
                            fecha = datetime.strptime(fecha_ren, fmt)
                            permiso_formateado['fecha_renovacion_formatted'] = fecha.strftime('%d/%m/%Y')
                            break
                        except:
                            continue
                    else:
                        permiso_formateado['fecha_renovacion_formatted'] = fecha_ren
                except:
                    permiso_formateado['fecha_renovacion_formatted'] = fecha_ren
            else:
                permiso_formateado['fecha_renovacion_formatted'] = 'N/A'
            
            # Asegurar que todos los campos tengan valor
            permiso_formateado['bloque'] = permiso.get('bloque', 'N/A')
            permiso_formateado['sucursal'] = permiso.get('sucursal', 'N/A')
            permiso_formateado['tipo_permiso'] = permiso.get('tipo_permiso', 'N/A')
            permiso_formateado['existencia'] = permiso.get('existencia', 'N/A')
            permiso_formateado['estatus'] = permiso.get('estatus', 'N/A')
            
            permisos_formateados.append(permiso_formateado)
        
        # Obtener nombre de usuario para el reporte
        nombre_usuario = "Usuario"
        if hasattr(current_user, 'nombre'):
            nombre_usuario = current_user.nombre
        elif hasattr(current_user, 'id'):
            nombre_usuario = current_user.id
        
        # Generar HTML del reporte
        fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        html = f'''
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reporte de Permisos - La Postal</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 0 20px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 3px solid #b71c1c;
                }}
                .header h1 {{
                    color: #b71c1c;
                    font-weight: 700;
                    margin-bottom: 5px;
                }}
                .header h2 {{
                    color: #333;
                    font-weight: 600;
                    margin-top: 0;
                }}
                .info-box {{
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 25px;
                    border-left: 4px solid #b71c1c;
                }}
                .table-responsive {{
                    margin-top: 20px;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 0;
                }}
                thead {{
                    background: linear-gradient(135deg, #b71c1c 0%, #d32f2f 100%);
                    color: white;
                }}
                th {{
                    padding: 15px;
                    text-align: left;
                    font-weight: 600;
                    border: none;
                }}
                td {{
                    padding: 12px 15px;
                    border-bottom: 1px solid #e0e0e0;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                tr:hover {{
                    background-color: #f0f0f0;
                }}
                .total-row {{
                    background-color: #2c3e50;
                    color: white;
                    font-weight: bold;
                }}
                .total-row td {{
                    padding: 15px;
                    border: none;
                }}
                .estatus-badge {{
                    padding: 5px 12px;
                    border-radius: 20px;
                    font-weight: 600;
                    font-size: 0.85rem;
                    display: inline-block;
                    min-width: 100px;
                    text-align: center;
                }}
                .vigente {{
                    background-color: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }}
                .vencido {{
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }}
                .en-tramite {{
                    background-color: #fff3cd;
                    color: #856404;
                    border: 1px solid #ffeaa7;
                }}
                .pendiente {{
                    background-color: #e2e3e5;
                    color: #383d41;
                    border: 1px solid #d6d8db;
                }}
                .proximo {{
                    background-color: #cce5ff;
                    color: #004085;
                    border: 1px solid #b8daff;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    text-align: center;
                    color: #666;
                    font-size: 0.9rem;
                }}
                .action-buttons {{
                    margin-top: 30px;
                    text-align: center;
                }}
                .btn-print {{
                    background: linear-gradient(135deg, #b71c1c 0%, #d32f2f 100%);
                    color: white;
                    border: none;
                    padding: 10px 25px;
                    border-radius: 5px;
                    font-weight: 600;
                    cursor: pointer;
                    margin-right: 10px;
                }}
                .btn-close {{
                    background: #6c757d;
                    color: white;
                    border: none;
                    padding: 10px 25px;
                    border-radius: 5px;
                    font-weight: 600;
                    cursor: pointer;
                }}
                @media print {{
                    .no-print {{
                        display: none;
                    }}
                    body {{
                        margin: 0;
                        padding: 0;
                        background: white;
                    }}
                    .container {{
                        box-shadow: none;
                        padding: 0;
                    }}
                    .action-buttons {{
                        display: none;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Reporte de Permisos - La Postal</h1>
                    <h2>{estatus_bd.title()}</h2>
                    <p><strong>Fecha de generaciÃ³n:</strong> {fecha_actual}</p>
                </div>
                
                <div class="info-box">
                    <div class="row">
                        <div class="col-md-4">
                            <p><strong>Filtro aplicado:</strong> {estatus_bd.title()}</p>
                        </div>
                        <div class="col-md-4">
                            <p><strong>Total de registros:</strong> {len(permisos_formateados)}</p>
                        </div>
                        <div class="col-md-4">
                            <p><strong>Generado por:</strong> {nombre_usuario}</p>
                            <p><strong>Departamento:</strong> PlaneaciÃ³n</p>
                        </div>
                    </div>
                </div>
                
                <div class="action-buttons no-print">
                    <button onclick="window.print()" class="btn-print">
                        Imprimir Reporte
                    </button>
                </div>
                
                <div class="table-responsive">
        '''
        
        if permisos_formateados:
            html += '''
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Bloque</th>
                                <th>Sucursal</th>
                                <th>Permiso</th>
                                <th>Existencia</th>
                                <th>Fecha ExpediciÃ³n</th>
                                <th>Fecha RenovaciÃ³n</th>
                                <th>Estatus</th>
                            </tr>
                        </thead>
                        <tbody>
            '''
            
            # Agregar filas de datos
            for i, permiso in enumerate(permisos_formateados, 1):
                estatus_text = permiso.get('estatus', '').upper()
                estatus_class = ""
                
                if 'VIGENT' in estatus_text:
                    estatus_class = 'vigente'
                elif 'VENCID' in estatus_text:
                    estatus_class = 'vencido'
                elif 'TRÃMITE' in estatus_text or 'TRAMITE' in estatus_text:
                    estatus_class = 'en-tramite'
                elif 'PENDIENT' in estatus_text:
                    estatus_class = 'pendiente'
                elif 'PRÃ“XIMO' in estatus_text or 'PROXIMO' in estatus_text:
                    estatus_class = 'proximo'
                else:
                    estatus_class = 'vigente'  
                
                html += f'''
                        <tr>
                            <td>{i}</td>
                            <td>{permiso.get('bloque', 'N/A')}</td>
                            <td>{permiso.get('sucursal', 'N/A')}</td>
                            <td>{permiso.get('tipo_permiso', 'N/A')}</td>
                            <td>{permiso.get('existencia', 'N/A')}</td>
                            <td>{permiso.get('fecha_expedicion_formatted', 'N/A')}</td>
                            <td>{permiso.get('fecha_renovacion_formatted', 'N/A')}</td>
                            <td><span class="estatus-badge {estatus_class}">{permiso.get('estatus', 'N/A')}</span></td>
                        </tr>
                '''
            
            html += f'''
                        </tbody>
                        <tfoot>
                            <tr class="total-row">
                                <td colspan="7" style="text-align: right;"><strong>Total de permisos:</strong></td>
                                <td><strong>{len(permisos_formateados)}</strong></td>
                            </tr>
                        </tfoot>
                    </table>
            '''
        else:
            html += '''
                    <div class="alert alert-warning text-center" style="padding: 30px; margin: 20px 0;">
                        <h4> No se encontraron permisos</h4>
                        <p>No hay registros que coincidan con el filtro aplicado.</p>
                    </div>
            '''
        
        html += f'''
                </div>
                
                <div class="footer">
                    <p>Sistema de GestiÃ³n de Permisos - La Postal Â© {datetime.now().year}</p>
                    <p>Este reporte fue generado automÃ¡ticamente por el sistema.</p>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                // Auto-imprimir al cargar (opcional, descomenta si lo quieres)
                // window.onload = function() {{
                //     setTimeout(function() {{
                //         window.print();
                //     }}, 1000);
                // }};
                
                // Mejorar experiencia de impresiÃ³n
                document.querySelector('.btn-print').addEventListener('click', function() {{
                    window.print();
                }});
                
                document.querySelector('.btn-close').addEventListener('click', function() {{
                    window.close();
                }});
            </script>
        </body>
        </html>
        '''
        
        print(f"Reporte generado exitosamente para {len(permisos_formateados)} permisos")
        return html
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error generando reporte: {str(e)}")
        print(f" Detalle del error:\n{error_detail}")
        
        # Mostrar error detallado en HTML
        error_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error en Reporte</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                .error-box {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>Error Generando Reporte</h1>
            <div class="error-box">
                <h3>Detalles del Error:</h3>
                <p><strong>Tipo:</strong> {type(e).__name__}</p>
                <p><strong>Mensaje:</strong> {str(e)}</p>
                <p><strong>Estatus solicitado:</strong> {estatus}</p>
            </div>
            <p><a href="javascript:history.back()">â† Volver</a></p>
        </body>
        </html>
        '''
        return error_html, 500

@app.route("/planeacion-reportes")
@login_required
def planeacion_reportes():
    """PÃ¡gina principal de reportes (en caso de que la necesites)"""
    return render_template("planeacion.html")

@app.route("/descargar-reporte/<estatus>/<formato>")
@login_required
def descargar_reporte(estatus, formato):
    """Descargar reporte en diferentes formatos (CSV, etc.)"""
    try:
        import requests
        import csv
        import io
        from datetime import datetime
        
        # ConfiguraciÃ³n Supabase
        SUPABASE_URL = 'https://uooffrtjajluvhcauctk.supabase.co'
        SUPABASE_KEY = 'sb_publishable_ib_7iPl1ccS0PGo3yKzggQ_nWMi9CU8'
        
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Mapear nombres de estatus
        estatus_map = {
            'vigentes': 'VIGENTE',
            'vencidos': 'VENCIDO',
            'en-tramite': 'EN TRÃMITE',
            'pendientes': 'PENDIENTE',
            'proximos-a-vencer': 'PRÃ“XIMO A VENCER'
        }
        
        estatus_bd = estatus_map.get(estatus.lower(), estatus.upper())
        
        # Obtener permisos filtrados
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/datos_financieros',
            headers=headers,
            params={
                'select': 'id,bloque,sucursal,tipo_permiso,existencia,fecha_expedicion,fecha_renovacion,estatus',
                'estatus': f'eq.{estatus_bd}',
                'order': 'sucursal.asc'
            }
        )
        
        if response.status_code != 200:
            return jsonify({'error': f'No se pudieron obtener los permisos {estatus}'}), 400
        
        permisos = response.json()
        
        fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f'reporte_permisos_{estatus}_{fecha_actual}'
        
        if formato == 'csv':
            # Generar CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Encabezados
            writer.writerow(['Reporte de Permisos - La Postal'])
            writer.writerow([f'Estatus: {estatus_bd}'])
            writer.writerow([f'Fecha de generaciÃ³n: {datetime.now().strftime("%d/%m/%Y %H:%M")}'])
            writer.writerow(['Generado por:', current_user.nombre])
            writer.writerow([])
            writer.writerow(['#', 'Bloque', 'Sucursal', 'Permiso', 'Existencia', 'Fecha ExpediciÃ³n', 'Fecha RenovaciÃ³n', 'Estatus'])
            
            # Datos
            for i, permiso in enumerate(permisos, 1):
                writer.writerow([
                    i,
                    permiso.get('bloque', ''),
                    permiso.get('sucursal', ''),
                    permiso.get('tipo_permiso', ''),
                    permiso.get('existencia', ''),
                    permiso.get('fecha_expedicion', ''),
                    permiso.get('fecha_renovacion', ''),
                    permiso.get('estatus', '')
                ])
            
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'{nombre_archivo}.csv'
            )
            
        else:
            # Por defecto, redirigir al reporte HTML
            return redirect(url_for('generar_reporte_permisos', estatus=estatus))
            
    except Exception as e:
        print(f"Error descargando reporte: {e}")
        return jsonify({'error': str(e)}), 500
    
# ==================== MAIN ====================
if __name__ == "__main__":
    app.run(debug=True)










