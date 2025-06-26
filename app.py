from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import pytz

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb+srv://admin:admin123@cluster0.2owahcw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["smart_parking"]
stats = db["estadisticas"]

tz = pytz.timezone("America/Argentina/Buenos_Aires")

@app.route("/api/estadisticas/update", methods=["POST"])
def update():
    data = request.get_json()

    tipo = data["tipo_vehiculo"]
    lugar = str(data["estacionamiento_id"])
    nombre = data.get("nombre", "")
    apellido = data.get("apellido", "")
    dni = data.get("dni", "")
    celular = data.get("celular", "")
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    ahora = datetime.now(tz)

    doc = stats.find_one({"_id": "estadisticas"}) or {
        "_id": "estadisticas",
        "por_tipo_vehiculo": {},
        "por_estacionamiento": {},
        "por_dia": {},
        "por_tipo_dia": {},
        "por_franja_horaria": {},
        "ultimos_usuarios": [],
        "total_registros": 0
    }

    # ====== MÉTRICAS GENERALES ======
    doc["por_tipo_vehiculo"][tipo] = doc["por_tipo_vehiculo"].get(tipo, 0) + 1
    doc["por_estacionamiento"][lugar] = doc["por_estacionamiento"].get(lugar, 0) + 1
    doc["total_registros"] += 1

    # Día del mes
    dia_mes = ahora.day
    doc["por_dia"][str(dia_mes)] = doc["por_dia"].get(str(dia_mes), 0) + 1

    # Día de la semana
    dia_semana = ahora.weekday()  # lunes = 0 ... domingo = 6
    tipo_dia = "Lunes a Viernes" if dia_semana < 5 else "Fin de Semana"
    doc["por_tipo_dia"][tipo_dia] = doc["por_tipo_dia"].get(tipo_dia, 0) + 1

    # Franja horaria
    hora = ahora.hour
    if 6 <= hora < 12:
        franja = "Mañana"
    elif 12 <= hora < 18:
        franja = "Tarde"
    elif 18 <= hora < 24:
        franja = "Noche"
    else:
        franja = "Madrugada"
    doc["por_franja_horaria"][franja] = doc["por_franja_horaria"].get(franja, 0) + 1

    # ====== HISTORIAL DE ÚLTIMOS USUARIOS ======
    nuevo_usuario = {
        "nombre": nombre,
        "apellido": apellido,
        "dni": dni,
        "celular": celular,
        "tipo_vehiculo": tipo,
        "estacionamiento_id": int(lugar),
        "start_time": start_time or ahora.isoformat(),
        "end_time": end_time  # puede ser null si sigue aparcado
    }

    usuarios = doc.get("ultimos_usuarios", [])
    usuarios.insert(0, nuevo_usuario)  # agrega al inicio
    doc["ultimos_usuarios"] = usuarios[:10]  # mantiene solo los 10 más recientes

    # ====== GUARDAR DOCUMENTO ======
    stats.replace_one({"_id": "estadisticas"}, doc, upsert=True)
    return jsonify({"message": "Estadísticas actualizadas"})

@app.route("/api/estadisticas", methods=["GET"])
def obtener():
    data = stats.find_one({"_id": "estadisticas"}, {"_id": 0})
    return jsonify(data or {})

if __name__ == "__main__":
    app.run()
