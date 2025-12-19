import os
import json
import unicodedata
import gspread
from datetime import datetime
import time
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, flash
from google.oauth2.service_account import Credentials
from werkzeug.exceptions import HTTPException
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from dotenv import load_dotenv, find_dotenv

# ==================== CONFIGURACIÓN INICIAL ====================
app = Flask(__name__)
app.secret_key = 'Lapostal01'

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

# USUARIOS - CONTRASEÑAS EN TEXTO PLANO
USUARIOS = {
    'C.E.O': {
        'password': 'Dpostal01',
        'nombre': 'Merlin Lara Arturo',
        'rol': 'C.E.O'
    },
    'Direccion': {
        'password': 'Dpostal01',
        'nombre': 'Pedraza  Jose Luis',
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
        'nombre': 'Sánchez Rangel Carlos Javier',
        'rol': 'Capacitador de Gerentes'
    },
    'Gerente Administración': {
        'password': 'GApostal01',
        'nombre': 'Abaroa Esqueda Leonardo',
        'rol': 'Gerente Administración'
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
        'nombre': 'Franco Alonzo  Jesus Omar',
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
    'Gerente supervision': {
        'password': 'GSpostal01',
        'nombre': 'Johana Meza',
        'rol': 'Gerente supervision'
    },
    'Gerente Recursos Humanos': {
        'password': 'GRHpostal01',
        'nombre': 'Garcia Rodriguez Genesis Clarise',
        'rol': 'Gerente RH'
    },
        'Ingenierio': {
        'password': 'Iapostal01',
        'nombre': 'Sanchez Gomez Jose Antonio',
        'rol': 'Ing de Proyectos/Procesos'
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

# ==================== AUTENTICACIÓN GOOGLE ====================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
load_dotenv(find_dotenv())
SHEET_NAME = os.getenv("SHEET_NAME")
GOOGLE_CREDS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")

if not GOOGLE_CREDS_FILE:
    raise RuntimeError("❌ La informacion de google_credentials.json no se encuentra disponible")

creds_data = json.loads(GOOGLE_CREDS_FILE)

if isinstance(creds_data, str):
  creds_data = json.loads(creds_data)

private_key = creds_data.get("private_key", "").strip()
if "\\n" in private_key:
    private_key = private_key.replace("\\n", "\n")
if private_key == "-----BEGIN PRIVATE KEY-----\n-----END PRIVATE KEY-----":
    raise RuntimeError("El bloque de la clave privada está vacío. Vuelve a descargarlo de Google Cloud.")
creds_data["private_key"] = private_key

creds = Credentials.from_service_account_info(creds_data, scopes=scope)
client = gspread.authorize(creds)
print("✅ Conexión exitosa con Google Sheets")

SHEET_NAME = "ventas"

# ==================== CACHÉS GLOBALES ====================
cache_sheets = {"data": None, "timestamp": 0}
cache_global = {"data": None, "timestamp": 0}
cache_comparativa = {"data": None, "timestamp": 0}
CACHE_TTL = 300

def get_spreadsheet_data():
    """Obtiene datos del spreadsheet con caché mejorado"""
    global cache_sheets
    now = time.time()
    
    if cache_sheets["data"] and (now - cache_sheets["timestamp"]) < CACHE_TTL:
        print("✅ Usando datos en caché (sheets)")
        return cache_sheets["data"]
    
    print("📡 Leyendo Google Sheets...")
    try:
        spreadsheet = client.open(SHEET_NAME)
        hojas = spreadsheet.worksheets()
        data = {}
        
        print(f"🔍 Hojas encontradas: {[hoja.title for hoja in hojas]}")
        
        # ✅ CORREGIDO: Leer TODAS las hojas, sin filtrar
        for hoja in hojas:
            try:
                print(f"📖 Leyendo: '{hoja.title}'")
                filas = hoja.get_all_values()
                data[hoja.title] = filas
                print(f"✅ '{hoja.title}': {len(filas)} filas")
            except Exception as e:
                print(f"❌ Error en '{hoja.title}': {e}")
                data[hoja.title] = []
        
        cache_sheets["data"] = data
        cache_sheets["timestamp"] = now
        return data
        
    except Exception as e:
        print(f"❌ Error general: {e}")
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
    """Normaliza encabezados/strings para comparaciones robustas (mayúsculas, sin acentos, espacios limpitos)."""
    if s is None:
        return ""
    s = str(s)
    # Primero quitar acentos
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    # Luego limpiar espacios y caracteres especiales
    s = s.replace("\u00A0", " ")  # NBSP
    s = " ".join(s.strip().split())
    # Convertir a mayúsculas y quitar caracteres problemáticos
    s = s.upper()
    s = s.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
    s = s.replace("Ñ", "N")
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
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ñ": "N",
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
# ==================== RUTAS DE AUTENTICACIÓN ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # DEBUG TEMPORAL
        print(f"🔍 USUARIO INGRESADO: '{username}'")
        print(f"🔍 CONTRASEÑA INGRESADA: '{password}'")
        
        if username in USUARIOS:
            print(f"🔍 CONTRASEÑA ESPERADA: '{USUARIOS[username]['password']}'")
            print(f"🔍 ¿COINCIDEN?: {USUARIOS[username]['password'] == password}")
        
        if username in USUARIOS and USUARIOS[username]['password'] == password:
            user = User(username, USUARIOS[username]['nombre'], USUARIOS[username]['rol'])
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('❌ Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('✅ Sesión cerrada correctamente', 'success')
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
@login_required
def home():
    # Si el usuario es "Grafica", redirigir directamente al reporte
    if current_user.id == 'Gerentes':
        return redirect(url_for('reporte_semanal_grafica'))
    
    # Para otros usuarios, mostrar el home normal
    return render_template("home.html")

# ==================== TABLA ====================
@app.route("/tabla", methods=["GET", "POST"])
@login_required
def tabla_completa():
    spreadsheet = client.open(SHEET_NAME)
    sucursales = [ws.title for ws in spreadsheet.worksheets()]

    sucursal_seleccionada = request.form.get("sucursal") or sucursales[0]
    fecha_inicio_str = request.form.get("fecha_inicio")
    fecha_fin_str = request.form.get("fecha_fin")

    fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date() if fecha_inicio_str else None
    fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date() if fecha_fin_str else None

    sheet = spreadsheet.worksheet(sucursal_seleccionada)
    all_rows = sheet.get_all_values()
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
    spreadsheet = client.open(SHEET_NAME)
    sucursales = [ws.title for ws in spreadsheet.worksheets()]
    sucursal_seleccionada = request.form.get("sucursal") or sucursales[0]
    sheet = spreadsheet.worksheet(sucursal_seleccionada)

    columnas_resumen = [
        'G.MES', 'G.TOTAL VENTA C/IVA', 'G.EFECTIVO', 'G.T.C.', 'G.UBER', 'G.PEDIDOS UBER',
        'G.DIDI TC', 'G.PEDIDOS DIDI', 'G.RAPPI TC', 'G.PEDIDOS RAPPI', 'G.TOTAL APPS',
        'G.TOTAL SUCURSAL', 'G.VENTA COMEDOR', 'G.CUENTAS COMEDOR', 'G.VENTA DOMICILIO',
        'G.CUENTAS DOMICILIO', 'G.VENTA RAPIDO', 'G.CUENTAS RAPIDO', 'G.TICKET PROMEDIO'
    ]

    all_rows = sheet.get_all_values()
    headers = [_norm(h) for h in all_rows[0]] if all_rows else []

    try:
        start_index = headers.index(_norm("G.MES"))
    except ValueError:
        return f"La hoja '{sucursal_seleccionada}' no contiene la columna 'G.MES'", 400

    end_index = start_index + len(columnas_resumen)
    indices = list(range(start_index, end_index))
    headers_finales = [ _norm(h) for h in columnas_resumen ]

    data = []
    for row in all_rows[1:]:
        fila = {}
        mes_valor = row[start_index].strip().upper() if start_index < len(row) else ""
        if mes_valor in ORDEN_MESES:
            for j, idx in enumerate(indices):
                fila[headers_finales[j]] = row[idx] if idx < len(row) else ""
            if any(fila.values()):
                data.append(fila)

    data = sorted(data, key=lambda x: ORDEN_MESES.index(x[_norm("G.MES")].upper()) if x.get(_norm("G.MES")) in ORDEN_MESES else 99)
    return render_template("resumen.html", sucursales=sucursales, sucursal_actual=sucursal_seleccionada, data=data)

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
        print(f"❌ Error en comparativa: {e}")
        return render_template("comparativa.html", 
                             sucursales=[],
                             sucursales_seleccionadas=[],
                             datos_comparativa=[],
                             error=f"Error: {str(e)}")

# ==================== DATOS PARA GRÁFICAS ====================
@app.route("/datos_grafica/<path:sucursal>")
@login_required
def datos_grafica(sucursal):
    try:
        sheet = client.open(SHEET_NAME).worksheet(sucursal)
        data = sheet.get_all_records()

        meses = [fila.get('G.MES') for fila in data if fila.get('G.MES')]
        uber = [num(fila.get('G.UBER', 0)) for fila in data if fila.get('G.MES')]
        didi = [num(fila.get('G.DIDI TC', 0)) for fila in data if fila.get('G.MES')]
        rappi = [num(fila.get('G.RAPPI TC', 0)) for fila in data if fila.get('G.MES')]
        comedor = [num(fila.get('G.VENTA COMEDOR', 0)) for fila in data if fila.get('G.MES')]
        domicilio = [num(fila.get('G.VENTA DOMICILIO', 0)) for fila in data if fila.get('G.MES')]
        rapido = [num(fila.get('G.VENTA RAPIDO', 0)) for fila in data if fila.get('G.MES')]

        pedidos_uber = [num_int(fila.get('G.PEDIDOS UBER', 0)) for fila in data if fila.get('G.MES')]
        pedidos_didi = [num_int(fila.get('G.PEDIDOS DIDI', 0)) for fila in data if fila.get('G.MES')]
        pedidos_rappi = [num_int(fila.get('G.PEDIDOS RAPPI', 0)) for fila in data if fila.get('G.MES')]

        cuentas_comedor = [num_int(fila.get('G.CUENTAS COMEDOR', 0)) for fila in data if fila.get('G.MES')]
        cuentas_domicilio = [num_int(fila.get('G.CUENTAS DOMICILIO', 0)) for fila in data if fila.get('G.MES')]
        cuentas_rapido = [num_int(fila.get('G.CUENTAS RAPIDO', 0)) for fila in data if fila.get('G.MES')]

        return jsonify({
            "meses": meses,
            "uber": uber,
            "didi": didi,
            "rappi": rappi,
            "comedor": comedor,
            "domicilio": domicilio,
            "rapido": rapido,
            "pedidos_uber": pedidos_uber,
            "pedidos_didi": pedidos_didi,
            "pedidos_rappi": pedidos_rappi,
            "cuentas_comedor": cuentas_comedor,
            "cuentas_domicilio": cuentas_domicilio,
            "cuentas_rapido": cuentas_rapido
        })
    except Exception as e:
        print("ERROR EN /datos_grafica:", e)
        return jsonify({"error": str(e)}), 500

# ==================== DATOS GLOBAL ====================
@app.route("/datos_grafica_global")
@login_required
def datos_grafica_global():
    global cache_global
    now = time.time()

    if cache_global["data"] and (now - cache_global["timestamp"] < CACHE_TTL):
        print("Usando datos globales en caché")
        return jsonify(cache_global["data"])

    try:
        spreadsheet = client.open(SHEET_NAME)
        hojas = spreadsheet.worksheets()

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

# ==================== DATOS PARA GRÁFICAS FILTRADAS (UNA SUCURSAL) ====================
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
    """Obtiene la última semana disponible"""
    hoy = datetime.now().date()
    lunes = hoy - timedelta(days=hoy.weekday())
    return lunes.strftime("%Y-%m-%d")

def obtener_datos_ranking(semana):
    """
    Obtiene los datos del ranking para una semana específica
    """
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
        print(f"❌ Error en obtener_datos_ranking: {e}")
        return []

def procesar_comparacion_automatica(datos_actual, datos_anterior, semana_actual, semana_anterior):
    """
    Combina los datos de ambas semanas para la comparación
    """
    datos_comparacion = []
    
    # Crear diccionarios para acceso rápido
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
    """
    Obtiene las fechas de inicio y fin para una semana específica
    """
    try:
        fecha_inicio = datetime.strptime(semana, "%Y-%m-%d").date()
        fecha_fin = fecha_inicio + timedelta(days=6)
        return fecha_inicio.strftime("%d/%m/%Y"), fecha_fin.strftime("%d/%m/%Y")
    except:
        return ("dd/mm/yyyy", "dd/mm/yyyy")

def generar_opciones_semanas():
    """Genera opciones de semanas para el selector (últimas 12 semanas)"""
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
        # Obtener la semana actual del formulario o usar la última disponible
        semana_actual = request.form.get("semana")
        
        if not semana_actual:
            semana_actual = obtener_ultima_semana()
        
        # Calcular semana anterior automáticamente
        try:
            fecha_actual = datetime.strptime(semana_actual, "%Y-%m-%d").date()
            fecha_anterior = fecha_actual - timedelta(days=7)
            semana_anterior = fecha_anterior.strftime("%Y-%m-%d")
        except:
            # Si hay error en el cálculo, usar semana anterior numérica
            semana_anterior = "semana-anterior"
        
        # Obtener datos de ambas semanas
        datos_actual = obtener_datos_ranking(semana_actual)
        datos_anterior = obtener_datos_ranking(semana_anterior)
        
        # Procesar comparación automática
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
        print(f"❌ Error en ranking: {e}")
        # En caso de error, mostrar página con datos vacíos
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

# ==================== REPORTE SEMANAL SIMPLIFICADO PARA USUARIO GRAFICA ====================
@app.route("/reporte-grafica")
@login_required
def reporte_semanal_grafica():
    # Verificar que el usuario sea "Grafica"
    if current_user.id != 'Gerentes':
        flash('❌ No tienes permisos para acceder a esta página', 'error')
        return redirect(url_for('home'))
    
    try:
        sheets_data = get_spreadsheet_data()
        sucursales = list(sheets_data.keys()) if sheets_data else []
        
        if not sucursales:
            return render_template("reporte_grafica.html",
                                 datos_semana_anterior=[],
                                 rango_semana="No disponible",
                                 error="No se pudieron cargar los datos")
        
        # Calcular semana ANTERIOR (lunes a domingo de la semana pasada)
        hoy = datetime.now().date()
        
        # Calcular lunes de esta semana y restar 7 días para ir a la semana anterior
        lunes_semana_actual = hoy - timedelta(days=hoy.weekday())
        lunes_semana_anterior = lunes_semana_actual - timedelta(days=7)
        domingo_semana_anterior = lunes_semana_anterior + timedelta(days=6)
        
        rango_semana = f"{lunes_semana_anterior.strftime('%d/%m/%Y')} al {domingo_semana_anterior.strftime('%d/%m/%Y')}"
        
        # Obtener datos de la SEMANA ANTERIOR para todas las sucursales
        datos_semana_anterior = []
        for sucursal in sucursales:
            if sucursal in sheets_data:
                data_rows = sheets_data[sucursal]
                
                if len(data_rows) > 1:
                    headers = [_norm(h) for h in data_rows[0]]
                    data_records = []
                    
                    # Filtrar datos de la SEMANA ANTERIOR
                    for row in data_rows[1:]:
                        if len(row) >= len(headers):
                            record = {headers[i]: row[i] for i in range(len(headers))}
                            
                            fecha_str = record.get('APERTURA', '')
                            fecha_row = parse_fecha(fecha_str)
                            
                            if fecha_row and lunes_semana_anterior <= fecha_row <= domingo_semana_anterior:
                                data_records.append(record)
                    
                    # Calcular total de la semana anterior
                    total_semanal = sum(num(fila.get('TOTAL SUCURSAL', 0)) for fila in data_records)
                    
                    datos_semana_anterior.append({
                        'nombre': sucursal,
                        'total_semanal': total_semanal
                    })
        
        # Ordenar por total (mayor a menor)
        datos_semana_anterior.sort(key=lambda x: x['total_semanal'], reverse=True)
        
        return render_template("reporte_grafica.html",
                             datos_semana_anterior=datos_semana_anterior,
                             rango_semana=rango_semana)  # ✅ CORREGIDO: rango_semana
                             
    except Exception as e:
        print(f"❌ Error en reporte gráfica: {e}")
        return render_template("reporte_grafica.html",
                             datos_semana_anterior=[],
                             rango_semana="Error",
                             error=f"Error: {str(e)}")
    
# ==================== MAIN ====================
if __name__ == "__main__":
    app.run(debug=True)