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
    doc = stats.find_one({"_id": "estadisticas"}) or {"_id": "estadisticas", "ultimos_usuarios": []}

    usuario = {
        "nombre": data.get("nombre"),
        "apellido": data.get("apellido"),
        "dni": data.get("dni"),
        "celular": data.get("celular"),
        "tipo_vehiculo": data.get("tipo_vehiculo"),
        "estacionamiento_id": data.get("estacionamiento_id"),
        "start_time": data.get("start_time"),
        "end_time": None,
        "ip": request.remote_addr
    }

    usuarios = doc.get("ultimos_usuarios", [])
    # Eliminar si ya existe para actualizar (evitar duplicados)
    usuarios = [u for u in usuarios if u["dni"] != usuario["dni"]]
    usuarios.insert(0, usuario)  # agregar al inicio
    usuarios = usuarios[:10]  # solo últimos 10

    doc["ultimos_usuarios"] = usuarios

    # Aquí puedes mantener otras estadísticas como antes, o agregarlas si quieres

    stats.replace_one({"_id": "estadisticas"}, doc, upsert=True)
    return jsonify({"message": "Usuario registrado"})

@app.route("/api/estadisticas/release", methods=["POST"])
def release():
    data = request.get_json()
    dni = data.get("dni")
    estacionamiento_id = data.get("estacionamiento_id")
    end_time = data.get("end_time")

    doc = stats.find_one({"_id": "estadisticas"})
    if not doc:
        return jsonify({"error": "No hay datos"}), 404

    usuarios = doc.get("ultimos_usuarios", [])
    for u in usuarios:
        if u["dni"] == dni and u["estacionamiento_id"] == estacionamiento_id and u.get("end_time") is None:
            u["end_time"] = end_time
            break

    doc["ultimos_usuarios"] = usuarios
    stats.replace_one({"_id": "estadisticas"}, doc)
    return jsonify({"message": "Usuario liberado"})

@app.route("/api/estadisticas", methods=["GET"])
def obtener():
    data = stats.find_one({"_id": "estadisticas"}, {"_id": 0})
    return jsonify(data or {})

if __name__ == "__main__":
    app.run()
