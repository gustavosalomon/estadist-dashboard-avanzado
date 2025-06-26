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

@app.route("/api/estadisticas/update", methods=["GET,POST"])
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
        "total_registros": 0
    }

    # Incrementar conteos
    doc["por_tipo_vehiculo"][tipo] = doc["por_tipo_vehiculo"].get(tipo, 0) + 1
    doc["por_estacionamiento"][lugar] = doc["por_estacionamiento"].get(lugar, 0) + 1

    # Día del mes (1-31)
    dia_mes = ahora.day
    doc["por_dia"][str(dia_mes)] = doc["por_dia"].get(str(dia_mes), 0) + 1

    doc["total_registros"] += 1

    stats.replace_one({"_id": "estadisticas"}, doc, upsert=True)

    return jsonify({"message": "Actualizado"})

@app.route("/api/estadisticas", methods=["GET"])
def obtener():
    data = stats.find_one({"_id": "estadisticas"}, {"_id": 0})
    return jsonify(data or {})

if __name__ == "__main__":
    app.run()
