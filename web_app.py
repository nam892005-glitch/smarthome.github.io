from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import json, os

app = Flask(__name__)
CORS(app)

# ===== CONFIG =====
MONGO_URI = "mongodb+srv://smarthome_user:123@cluster0.3s47ygi.mongodb.net/"
mongo = MongoClient(MONGO_URI)
db = mongo["smarthome"]
logs_col = db["logs"]

BROKER = "broker.emqx.io"
last_status = {"result": "--"}

# ===== MQTT RECEIVE =====
mqtt_client = mqtt.Client()

def on_connect(c,u,f,rc):
    c.subscribe("smarthome/+/status")

def on_message(c,u,msg):
    global last_status
    last_status = json.loads(msg.payload.decode())

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER,1883,60)
mqtt_client.loop_start()

# ===== API =====

@app.route("/")
def home():
    return "SmartHome API Running"

@app.route("/door", methods=["POST"])
def door():
    publish.single("smarthome/door/cmd",
                   json.dumps({"user": "web"}),
                   hostname=BROKER, port=1883)
    return jsonify({"msg": "door sent"})

@app.route("/light", methods=["POST"])
def light():
    data = request.json
    state = data.get("state","ON")

    publish.single("smarthome/light/cmd",
                   json.dumps({"user":"web","state":state}),
                   hostname=BROKER, port=1883)

    return jsonify({"msg": "light sent"})

@app.route("/status")
def status():
    return jsonify(last_status)

@app.route("/logs")
def logs():
    return jsonify(list(logs_col.find({},{"_id":0}).sort("time",-1).limit(20)))

# ===== RUN =====
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
