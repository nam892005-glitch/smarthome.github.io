from flask import Flask, render_template, request, redirect, session, jsonify
from pymongo import MongoClient
import paho.mqtt.publish as publish
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret"

# MongoDB
MONGO_URI = "mongodb+srv://smarthome_user:123@cluster0.3s47ygi.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["smarthome"]
users_col = db["users"]
logs_col = db["logs"]

BROKER = "broker.emqx.io"

# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = users_col.find_one({"username": request.form["username"], "password": request.form["password"]})
        if user:
            session["user"] = user["username"]
            session["role"] = user["role"]
            return redirect("/dashboard")
    return render_template("login.html")

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html", role=session["role"])

# GỬI LỆNH MQTT
def send_mqtt(topic, payload):
    publish.single(topic, json.dumps(payload), hostname=BROKER, port=1883)

@app.route("/light", methods=["POST"])
def light():
    state = request.form["state"]
    send_mqtt("smarthome/light/cmd", {"user": session["user"], "state": state})
    return "OK"

@app.route("/door", methods=["POST"])
def door():
    send_mqtt("smarthome/door/cmd", {"user": session["user"], "action": "open"})
    return "OK"

# LOGS API
@app.route("/logs")
def logs():
    data = list(logs_col.find({}, {"_id":0}).sort("time",-1))
    return jsonify(data)

# USER MANAGEMENT (ADMIN)
@app.route("/users")
def users():
    if session.get("role") != "admin":
        return "Forbidden"
    return render_template("users.html", users=list(users_col.find({}, {"_id":0})))

@app.route("/add_user", methods=["POST"])
def add_user():
    users_col.insert_one({
        "username": request.form["username"],
        "password": request.form["password"],
        "role": request.form["role"]
    })
    return redirect("/users")

@app.route("/delete_user/<username>")
def delete_user(username):
    users_col.delete_one({"username": username})
    return redirect("/users")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
