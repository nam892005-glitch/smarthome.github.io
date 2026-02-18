from flask import Flask, render_template, request, redirect, session, jsonify
from pymongo import MongoClient
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import json, os

app = Flask(__name__)
app.secret_key = "namhome_secret"

# ================== CONFIG ==================
BROKER = "broker.emqx.io"

MONGO_URI = "mongodb+srv://smarthome_user:123@cluster0.3s47ygi.mongodb.net/"
mongo = MongoClient(MONGO_URI)
db = mongo["smarthome"]
users_col = db["users"]
logs_col = db["logs"]

last_status = {"result": "--"}

# ================== RECEIVE STATUS ==================
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("🌍 WEB MQTT CONNECTED:", rc)
    client.subscribe("namhome/+/status")

def on_message(client, userdata, msg):
    global last_status
    last_status = json.loads(msg.payload.decode())
    print("🌍 WEB RECEIVED STATUS:", last_status)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER, 1883, 60)
mqtt_client.loop_start()

# ================== LOGIN ==================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        user = users_col.find_one({"username":u,"password":p})
        if user:
            session["user"] = u
            session["role"] = user["role"]
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html",
                           user=session["user"],
                           role=session["role"])

# ================== CONTROL ==================
@app.route("/door", methods=["POST"])
def door():
    publish.single("namhome/door/cmd",
                   json.dumps({"user":session["user"]}),
                   hostname=BROKER, port=1883)
    return "OK"

@app.route("/light", methods=["POST"])
def light():
    state = request.form["state"]
    publish.single("namhome/light/cmd",
                   json.dumps({
                       "user":session["user"],
                       "state":state
                   }),
                   hostname=BROKER, port=1883)
    return "OK"

@app.route("/status")
def status():
    return jsonify(last_status)

# ================== LOGS ==================
@app.route("/logs")
def logs():
    if "user" not in session:
        return redirect("/")
    data = list(logs_col.find({},{"_id":0}).sort("time",-1).limit(50))
    return render_template("logs.html", logs=data)

# ================== ADMIN ==================
@app.route("/users")
def users():
    if session.get("role") != "admin":
        return "No permission"
    return render_template("users.html",
                           users=list(users_col.find({},{"_id":0})))

@app.route("/add_user", methods=["POST"])
def add_user():
    users_col.insert_one({
        "username":request.form["username"],
        "password":request.form["password"],
        "role":request.form["role"]
    })
    return redirect("/users")

@app.route("/delete/<u>")
def delete(u):
    users_col.delete_one({"username":u})
    return redirect("/users")

@app.route("/seed_admin")
def seed_admin():
    users_col.update_one(
        {"username":"admin"},
        {"$set":{
            "username":"admin",
            "password":"123456",
            "role":"admin"
        }},
        upsert=True
    )
    return "Admin created: admin / 123456"

if __name__ == "__main__":
    app.run(host="0.0.0.0",
            port=int(os.environ.get("PORT",10000)))
