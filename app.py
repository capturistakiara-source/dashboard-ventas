import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv

# ==================== 🧠 CACHÉ GLOBAL ====================
cache_sheets = {"data": None, "timestamp": 0}
CACHE_TTL = 120  # segundos (2 minutos)

def get_sheet_data():
    global cache_sheets
    now = time()

    if cache_sheets["data"] and (now - cache_sheets["timestamp"]) < CACHE_TTL:
        print("📦 Usando datos en caché")
        return cache_sheets["data"]

    print("📡 Leyendo Google Sheets...")
    spreadsheet = client.open(SHEET_NAME)
    hojas = spreadsheet.worksheets()
    data = {hoja.title: hoja.get_all_values() for hoja in hojas}

    cache_sheets["data"] = data
    cache_sheets["timestamp"] = now
    return data

app = Flask(__name__)

# ==================== 🔐 AUTENTICACIÓN LOCAL (Google Auth moderno, con corrección robusta) ====================
import os, json, gspread
from google.oauth2.service_account import Credentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

load_dotenv()
SHEET_NAME = os.getenv("SHEET_NAME")  # 🧾 Nombre de tu Google Sheet principal
GOOGLE_CREDS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")

if not GOOGLE_CREDS_FILE:
    raise RuntimeError("❌ La informacion de google_credentials.json no se encuentra disponible")

# Cargar JSON
creds_data = json.loads(GOOGLE_CREDS_FILE)
if isinstance(creds_data, str):
  creds_data = json.loads(creds_data)

# 🔧 Asegurar que la clave privada tenga saltos de línea reales
private_key = creds_data.get("private_key", "").strip()

# Si los saltos están escapados (\\n), los reparamos
if "\\n" in private_key:
    private_key = private_key.replace("\\n", "\n")

# ⚠️ Si se perdió el contenido interno, intenta recuperarlo
if private_key == "-----BEGIN PRIVATE KEY-----\n-----END PRIVATE KEY-----":
    raise RuntimeError("❌ El bloque de la clave privada está vacío. Revisa el archivo JSON original o vuelve a descargarlo desde Google Cloud.")

creds_data["private_key"] = private_key

# 🧩 Vista previa
print("🔑 Vista previa de la clave (primeras 2 líneas):")
print("\n".join(private_key.splitlines()[:3]))
print("————————————————————————————————————————")

# Crear credenciales y cliente
creds = Credentials.from_service_account_info(creds_data, scopes=scope)
client = gspread.authorize(creds)
print("✅ Conexión exitosa con Google Sheets")

# ==================== 📋 COLUMNAS ====================
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

# ==================== 🧮 FUNCIONES ====================
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
    """Convierte fechas tipo d/m/yyyy o yyyy-mm-dd a objeto date."""
    if not fecha_str:
        return None
    fecha_str = fecha_str.split(" ")[0]
    try:
        return datetime.strptime(fecha_str.strip(), "%d/%m/%Y").date()
    except ValueError:
        try:
            return datetime.strptime(fecha_str.strip(), "%Y-%m-%d").date()
        except:
            return None

# ==================== 🏠 RUTA HOME ====================
@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("home.html")

# ==================== 📅 TABLA CON FILTRO CORRECTO ====================
@app.route("/tabla", methods=["GET", "POST"])
def tabla_completa():
    spreadsheet = client.open(SHEET_NAME)
    sucursales = [ws.title for ws in spreadsheet.worksheets()]

    # 📌 Sucursal y fechas seleccionadas
    sucursal_seleccionada = request.form.get("sucursal") or sucursales[0]
    fecha_inicio_str = request.form.get("fecha_inicio")
    fecha_fin_str = request.form.get("fecha_fin")

    fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date() if fecha_inicio_str else None
    fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date() if fecha_fin_str else None

    # 📄 Leer datos de la sucursal seleccionada
    sheet = spreadsheet.worksheet(sucursal_seleccionada)
    all_rows = sheet.get_all_values()
    headers = [h.strip().upper() for h in all_rows[0]]
    columnas_upper = [c.upper() for c in COLUMNAS_COMPLETAS]

    indices = [headers.index(col) for col in columnas_upper if col in headers]
    headers_finales = [col for col in columnas_upper if col in headers]

    data = []
    for row in all_rows[1:]:
        fila = {headers_finales[j]: (row[idx].strip() if idx < len(row) else "") for j, idx in enumerate(indices)}

        # 🧭 Filtrar por rango de fechas usando parse_fecha
        fecha_row = parse_fecha(fila.get('APERTURA', ''))
        if not fecha_row:
            continue

        # ✅ APLICAR FILTRO
        if fecha_inicio and fecha_fin:
            if fecha_inicio <= fecha_row <= fecha_fin:
                data.append(fila)
        else:
            # Si no hay filtro, muestra todo
            data.append(fila)

    # ==================== 📊 SUMAR CAMPOS ====================
    columnas_a_sumar = [
        'TOTAL VENTA C/IVA', 'EFECTIVO', 'T.C.', 'UBER', 'PEDIDOS UBER',
        'DIDI TC', 'PEDIDOS DIDI', 'RAPPI TC', 'PEDIDOS RAPPI', 'TOTAL APPS',
        'TOTAL SUCURSAL', 'VENTA COMEDOR', 'CUENTAS COMEDOR',
        'VENTA DOMICILIO', 'CUENTAS DOMICILIO', 'VENTA RAPIDO',
        'CUENTAS RAPIDO', 'TICKET PROMEDIO'
    ]
    totales = {col: 0.0 for col in columnas_a_sumar}

    for fila in data:
        for col in columnas_a_sumar:
            valor_str = str(fila.get(col, "")).replace(",", "").replace("$", "").strip()
            if valor_str:
                try:
                    totales[col] += float(valor_str)
                except ValueError:
                    pass

    # 🧹 Ordenar la tabla por fecha ascendente
    data = sorted(data, key=lambda x: parse_fecha(x['APERTURA']) or datetime.min.date())

    return render_template(
        "tabla.html",
        sucursales=sucursales,
        sucursal_actual=sucursal_seleccionada,
        data=data,
        totales=totales,
        fecha_inicio=fecha_inicio_str,
        fecha_fin=fecha_fin_str
    )

# ==================== 📊 RESUMEN MENSUAL ====================
@app.route("/resumen", methods=["GET", "POST"])
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
    headers = [h.strip().upper() for h in all_rows[0]]

    try:
        start_index = headers.index("G.MES")
    except ValueError:
        return f"❌ La hoja '{sucursal_seleccionada}' no contiene la columna 'G.MES'", 400

    end_index = start_index + len(columnas_resumen)
    indices = list(range(start_index, end_index))
    headers_finales = columnas_resumen

    data = []
    for row in all_rows[1:]:
        fila = {}
        mes_valor = row[start_index].strip().upper() if start_index < len(row) else ""
        if mes_valor in ORDEN_MESES:
            for j, idx in enumerate(indices):
                fila[headers_finales[j]] = row[idx] if idx < len(row) else ""
            if any(fila.values()):
                data.append(fila)

    data = sorted(data, key=lambda x: ORDEN_MESES.index(x["G.MES"].upper()) if x["G.MES"].upper() in ORDEN_MESES else 99)

    return render_template("resumen.html", sucursales=sucursales, sucursal_actual=sucursal_seleccionada, data=data)

# ==================== 📈 DATOS PARA GRÁFICAS ====================
@app.route("/datos_grafica/<path:sucursal>")
def datos_grafica(sucursal):
    try:
        sheet = client.open(SHEET_NAME).worksheet(sucursal)
        data = sheet.get_all_records()

        meses = [fila['G.MES'] for fila in data if fila['G.MES']]
        uber = [num(fila['G.UBER']) for fila in data if fila['G.MES']]
        didi = [num(fila['G.DIDI TC']) for fila in data if fila['G.MES']]
        rappi = [num(fila['G.RAPPI TC']) for fila in data if fila['G.MES']]
        comedor = [num(fila['G.VENTA COMEDOR']) for fila in data if fila['G.MES']]
        domicilio = [num(fila['G.VENTA DOMICILIO']) for fila in data if fila['G.MES']]
        rapido = [num(fila['G.VENTA RAPIDO']) for fila in data if fila['G.MES']]

        pedidos_uber = [num_int(fila['G.PEDIDOS UBER']) for fila in data if fila['G.MES']]
        pedidos_didi = [num_int(fila['G.PEDIDOS DIDI']) for fila in data if fila['G.MES']]
        pedidos_rappi = [num_int(fila['G.PEDIDOS RAPPI']) for fila in data if fila['G.MES']]

        cuentas_comedor = [num_int(fila['G.CUENTAS COMEDOR']) for fila in data if fila['G.MES']]
        cuentas_domicilio = [num_int(fila['G.CUENTAS DOMICILIO']) for fila in data if fila['G.MES']]
        cuentas_rapido = [num_int(fila['G.CUENTAS RAPIDO']) for fila in data if fila['G.MES']]

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
        print("❌ ERROR EN /datos_grafica:", e)
        return jsonify({"error": str(e)}), 500

# ==================== 🌎 DATOS GLOBAL ====================
@app.route("/datos_grafica_global")
def datos_grafica_global():
    global cache_global
    now = time.time()

    if cache_global["data"] and (now - cache_global["timestamp"] < CACHE_TTL):
        print("📦 Usando datos en caché")
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

            total = 0
            ticket = 0
            contador = 0

            for fila in data:
                if fila.get('G.TOTAL SUCURSAL') and fila.get('G.TICKET PROMEDIO'):
                    total += num(fila['G.TOTAL SUCURSAL'])
                    ticket += num(fila['G.TICKET PROMEDIO'])
                    contador += 1

            if contador > 0:
                nombres_sucursales.append(nombre)
                totales_sucursal.append(total)
                ticket_promedio.append(round(ticket / contador, 2))

        response = {
            "sucursales": nombres_sucursales,
            "totales": totales_sucursal,
            "ticket_promedio": ticket_promedio
        }

        cache_global["data"] = response
        cache_global["timestamp"] = now

        return jsonify(response)
    except Exception as e:
        print("❌ Error global:", e)
        return jsonify({"error": str(e)}), 500

# ==================== 🧯 ERRORES ====================
@app.errorhandler(Exception)
def handle_error(e):
    print(f"❌ Error global: {e}")
    return jsonify({"error": str(e)}), 500

# ==================== 📈 DATOS PARA GRÁFICAS FILTRADAS ====================
@app.route("/datos_grafica_filtrada", methods=["POST"])
def datos_grafica_filtrada():
    sucursal = request.form.get("sucursal")
    fecha_inicio_str = request.form.get("fecha_inicio")
    fecha_fin_str = request.form.get("fecha_fin")

    fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date() if fecha_inicio_str else None
    fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date() if fecha_fin_str else None

    sheet = client.open(SHEET_NAME).worksheet(sucursal)
    all_rows = sheet.get_all_values()
    headers = [h.strip().upper() for h in all_rows[0]]

    # Todas las columnas que podrían graficarse
    columnas = [col for col in headers if col in COLUMNAS_COMPLETAS]
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

        # Agregar valores de cada métrica a su serie
        for col in columnas:
            valor = row[indices[col]] if col in indices else 0
            series[col].append(num(valor))

    return jsonify({
        "fechas": fechas,
        "series": series
    })

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')
    
# ==================== 🚀 INICIO ====================
if __name__ == "__main__":
    app.run(debug=True)
