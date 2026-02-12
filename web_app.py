from flask import Flask, render_template, request, redirect, session, jsonify
from pymongo import MongoClient
import paho.mqtt.client as mqtt
import json

app = Flask(__name__)
app.secret_key = "smarthome_secret"

MONGO_URI = "mongodb+srv://smarthome_user:123@cluster0.3s47ygi.mongodb.net/"
mongo = MongoClient(MONGO_URI)
db = mongo["smarthome"]
users_col = db["users"]
logs_col = db["logs"]

# MQTT client
mqtt_client = mqtt.Client(protocol=mqtt.MQTTv311)
mqtt_client.connect("broker.emqx.io", 1883, 60)
mqtt_client.loop_start()


# -------- LOGIN --------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = users_col.find_one({
            "username": request.form["username"],
            "password": request.form["password"]
        })
        if user:
            session["user"] = user["username"]
            session["role"] = user["role"]
            return redirect("/dashboard")
    return render_template("login.html")


# -------- DASHBOARD --------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html", user=session["user"], role=session["role"])


# -------- MQTT ROUTES --------
@app.route("/light", methods=["POST"])
def light():
    data = {
        "user": session["user"],
        "state": request.form["state"]
    }
    print("Publishing:", data)
    mqtt_client.publish("namhome/light/cmd", json.dumps(data))
    return redirect("/dashboard")


@app.route("/door", methods=["POST"])
def door():
    data = {"user": session["user"]}
    mqtt_client.publish("namhome/door/cmd", json.dumps(data))
    return redirect("/dashboard")


# -------- LOGS API --------
@app.route("/logs")
def logs():
    logs = list(logs_col.find({}, {"_id":0}).sort("time",-1).limit(20))
    return jsonify(logs)


# -------- USER MANAGEMENT (ADMIN) --------
@app.route("/users")
def users():
    if session.get("role") != "admin":
        return "Unauthorized", 403
    return render_template("users.html", users=list(users_col.find({}, {"_id":0})))


@app.route("/add_user", methods=["POST"])
def add_user():
    if session.get("role") != "admin":
        return "Unauthorized", 403
    users_col.insert_one({
        "username": request.form["username"],
        "password": request.form["password"],
        "role": request.form["role"]
    })
    return redirect("/users")


@app.route("/delete_user/<username>")
def delete_user(username):
    if session.get("role") != "admin":
        return "Unauthorized", 403
    users_col.delete_one({"username": username})
    return redirect("/users")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)

