from flask import Flask, render_template, request, redirect, session
import paho.mqtt.client as mqtt
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "smarthome_secret"

# ===== MongoDB =====
client = MongoClient("mongodb+srv://smarthome_user:123@cluster0.3s47ygi.mongodb.net/")
db = client["smarthome"]
users_col = db["users"]
logs_col = db["logs"]

# ===== MQTT =====
mqtt_client = mqtt.Client()
mqtt_client.connect("broker.emqx.io", 1883, 60)
mqtt_client.loop_start()

# ===== Login =====
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pw = request.form["password"]
        u = users_col.find_one({"username": user, "password": pw})
        if u:
            session["user"] = user
            session["role"] = u["role"]
            return redirect("/dashboard")
    return render_template("login.html")

# ===== Dashboard =====
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html", user=session["user"], role=session["role"])

# ===== Door =====
@app.route("/door/open")
def door_open():
    mqtt_client.publish("namhome/door/cmd", '{"user":"%s"}' % session["user"])
    return redirect("/dashboard")

# ===== Light =====
@app.route("/light/on")
def light_on():
    mqtt_client.publish("namhome/light/cmd", '{"user":"%s","state":"ON"}' % session["user"])
    return redirect("/dashboard")

@app.route("/light/off")
def light_off():
    mqtt_client.publish("namhome/light/cmd", '{"user":"%s","state":"OFF"}' % session["user"])
    return redirect("/dashboard")

# ===== Logs =====
@app.route("/logs")
def logs():
    data = logs_col.find().sort("time", -1)
    return render_template("logs.html", logs=data)

# ===== Admin user control =====
@app.route("/users", methods=["GET", "POST"])
def users():
    if session.get("role") != "admin":
        return redirect("/dashboard")

    if request.method == "POST":
        new_user = request.form["username"]
        pw = request.form["password"]
        users_col.insert_one({"username": new_user, "password": pw, "role": "member"})

    all_users = users_col.find()
    return render_template("users.html", users=all_users)

@app.route("/delete/<username>")
def delete_user(username):
    if session.get("role") == "admin":
        users_col.delete_one({"username": username})
    return redirect("/users")

# ===== Logout =====
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
