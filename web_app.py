from flask import Flask, render_template, request, redirect, session, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import paho.mqtt.client as mqtt
import json, os

app = Flask(__name__)
app.secret_key = "smarthome_secret"
CORS(app)

# ===== MongoDB =====
client = MongoClient(os.getenv("MONGO_URI"))
db = client["smarthome"]
users_col = db["users"]
logs_col = db["logs"]

# ===== MQTT (WEBSOCKET CHO RENDER) =====
def on_connect(client, userdata, flags, rc):
    print("WEB MQTT CONNECTED:", rc)

mqtt_client = mqtt.Client(transport="websockets")
mqtt_client.ws_set_options(path="/mqtt")
mqtt_client.on_connect = on_connect
mqtt_client.connect("broker.emqx.io", 8083, 60)
mqtt_client.loop_start()

# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]
        u = users_col.find_one({"username": user, "password": pwd})
        if u:
            session["user"] = user
            session["role"] = u["role"]
            return redirect("/dashboard")
    return render_template("login.html")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html")

# ================= CONTROL =================
@app.route("/door", methods=["POST"])
def door():
    mqtt_client.publish("namhome/door/cmd",
                        json.dumps({"user": session["user"]}))
    return "OK"

@app.route("/light", methods=["POST"])
def light():
    state = request.form["state"]
    mqtt_client.publish("namhome/light/cmd",
                        json.dumps({"user": session["user"], "state": state}))
    return "OK"

# ================= LOGS =================
@app.route("/logs")
def logs():
    data = list(logs_col.find({}, {"_id": 0}).sort("time", -1).limit(20))
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
