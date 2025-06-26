from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import pytz

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb+srv://admin:admin123@cluster0.2owahcw.mongodb.net/?retryWrites=true&w=majority")
db = client["smart_parking"]
stats = db["estadisticas"]

tz = pytz.timezone("America/Argentina/Buenos_Aires")

@app.route("/api/estadisticas/update", methods=["POST"])
def update():
    data = request.get_json()
    tipo = data["tipo_vehiculo"]
    lugar = str(data["estacionamiento_id"])
    ahora = datetime.now(tz)

    doc = stats.find_one({"_id": "estadisticas"}) or {
        "_id": "estadisticas",
        "por_tipo_vehiculo": {},
        "por_estacionamiento": {},
        "por_dia": {},
        "ultimos_usuarios": [],
        "total_registros": 0
    }

    # Actualiza conteos
    doc["por_tipo_vehiculo"][tipo] = doc["por_tipo_vehiculo"].get(tipo, 0) + 1
    doc["por_estacionamiento"][lugar] = doc["por_estacionamiento"].get(lugar, 0) + 1

    # Día del mes
    dia_mes = ahora.day
    doc["por_dia"][str(dia_mes)] = doc["por_dia"].get(str(dia_mes), 0) + 1

    # Actualizar ultimos_usuarios
    usuario = {
        "nombre": data.get("nombre", "Desconocido"),
        "apellido": data.get("apellido", "Desconocido"),
        "dni": data.get("dni", "Desconocido"),
        "celular": data.get("celular", "Desconocido"),
        "tipo_vehiculo": tipo,
        "estacionamiento_id": lugar,
        "start_time": data.get("start_time", ahora.isoformat()),
        "end_time": data.get("end_time")  # puede ser None o string
    }

    # Buscar si ya existe registro para ese DNI sin end_time
    lista = doc.get("ultimos_usuarios", [])
    existente_index = next((i for i, u in enumerate(lista) if u["dni"] == usuario["dni"] and u["end_time"] is None), None)

    if existente_index is not None:
        # Actualiza end_time si viene (liberar parking)
        if usuario["end_time"]:
            lista[existente_index]["end_time"] = usuario["end_time"]
    else:
        # Agrega nuevo usuario al inicio
        lista.insert(0, usuario)
        # Limita a últimos 10
        lista = lista[:10]

    doc["ultimos_usuarios"] = lista
    doc["total_registros"] += 1

    stats.replace_one({"_id": "estadisticas"}, doc, upsert=True)

    return jsonify({"message": "Actualizado"})

if __name__ == "__main__":
    app.run()
