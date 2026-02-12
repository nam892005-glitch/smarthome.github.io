from flask import Flask, render_template, request, redirect, session, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import paho.mqtt.client as mqtt
import json, os, datetime

app = Flask(__name__)
app.secret_key = "smarthome_secret"
CORS(app)

# ===== MongoDB =====
client = MongoClient(os.getenv("MONGO_URI"))
db = client["smarthome"]
users_col = db["users"]
logs_col = db["logs"]

# ===== MQTT =====
mqtt_client = mqtt.Client()
mqtt_client.connect("broker.emqx.io", 1883, 60)
mqtt_client.loop_start()


# ========== LOGIN ==========
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


# ========== DASHBOARD ==========
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html", user=session["user"], role=session["role"])


# ========== CONTROL ==========
@app.route("/door", methods=["POST"])
def door():
    mqtt_client.publish("namhome/door/cmd", json.dumps({"user": session["user"]}))
    return "OK"

@app.route("/light", methods=["POST"])
def light():
    state = request.form["state"]
    mqtt_client.publish("namhome/light/cmd", json.dumps({"user": session["user"], "state": state}))
    return "OK"


# ========== LOGS ==========
@app.route("/logs")
def logs():
    data = list(logs_col.find({}, {"_id": 0}).sort("time", -1).limit(30))
    return jsonify(data)


# ========== USER MGMT ==========
@app.route("/users")
def users():
    if session["role"] != "admin":
        return "No permission"
    data = list(users_col.find({}, {"_id": 0}))
    return render_template("users.html", users=data)

@app.route("/add_user", methods=["POST"])
def add_user():
    users_col.insert_one({
        "username": request.form["username"],
        "password": request.form["password"],
        "role": request.form["role"]
    })
    return redirect("/users")

@app.route("/delete_user/<u>")
def delete_user(u):
    users_col.delete_one({"username": u})
    return redirect("/users")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
