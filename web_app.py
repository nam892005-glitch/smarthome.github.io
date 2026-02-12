from flask import Flask, render_template, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import paho.mqtt.client as mqtt
import datetime, os, json

app = Flask(__name__)
CORS(app)

# ===== MongoDB =====
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["smarthome"]
logs_collection = db["logs"]

# ===== MQTT (WEBSOCKET CHO RENDER) =====
def on_connect(client, userdata, flags, rc):
    print("🌍 WEB MQTT Connected:", rc)

mqtt_client = mqtt.Client(transport="websockets")
mqtt_client.ws_set_options(path="/mqtt")
mqtt_client.on_connect = on_connect
mqtt_client.connect("broker.emqx.io", 8083, 60)
mqtt_client.loop_start()

def send_cmd(topic, data):
    mqtt_client.publish(topic, json.dumps(data))

# ===== ROUTES =====
@app.route("/")
def home():
    return render_template("dashboard.html")

@app.route("/open_door", methods=["POST"])
def open_door():
    send_cmd("namhome/door/cmd", {"user": "quan", "action": "open"})
    return jsonify({"status": "Door command sent"})

@app.route("/light_on", methods=["POST"])
def light_on():
    send_cmd("namhome/light/cmd", {"user": "quan", "state": "ON"})
    return jsonify({"status": "Light ON command sent"})

@app.route("/light_off", methods=["POST"])
def light_off():
    send_cmd("namhome/light/cmd", {"user": "quan", "state": "OFF"})
    return jsonify({"status": "Light OFF command sent"})

@app.route("/logs")
def get_logs():
    logs = list(logs_collection.find({}, {"_id": 0}).sort("time", -1).limit(20))
    return jsonify(logs)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
