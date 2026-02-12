from flask import Flask, render_template, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import paho.mqtt.client as mqtt
import datetime
import os

app = Flask(__name__)
CORS(app)

# ================== MongoDB ==================
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["smarthome"]
logs_collection = db["logs"]

# ================== MQTT ==================
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "smarthome/control"

mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

# ================== ROUTES ==================

@app.route("/")
def home():
    return render_template("dashboard.html")

@app.route("/open_door", methods=["POST"])
def open_door():
    mqtt_client.publish(MQTT_TOPIC, "OPEN_DOOR")

    logs_collection.insert_one({
        "action": "open_door",
        "time": datetime.datetime.utcnow()
    })

    return jsonify({"status": "Door opened"})


@app.route("/light_on", methods=["POST"])
def light_on():
    mqtt_client.publish(MQTT_TOPIC, "LIGHT_ON")

    logs_collection.insert_one({
        "action": "light_on",
        "time": datetime.datetime.utcnow()
    })

    return jsonify({"status": "Light ON"})


@app.route("/light_off", methods=["POST"])
def light_off():
    mqtt_client.publish(MQTT_TOPIC, "LIGHT_OFF")

    logs_collection.insert_one({
        "action": "light_off",
        "time": datetime.datetime.utcnow()
    })

    return jsonify({"status": "Light OFF"})


@app.route("/logs", methods=["GET"])
def get_logs():
    logs = list(logs_collection.find({}, {"_id": 0}))
    return jsonify(logs)


# ================== RUN ==================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
