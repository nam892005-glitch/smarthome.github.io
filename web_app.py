from flask import Flask, render_template, request, redirect, session
import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json

app = Flask(__name__)
app.secret_key = "smarthome_secret"

# ================= MONGODB =================
client_db = MongoClient(
    "mongodb+srv://smarthome_user:123@cluster0.3s47ygi.mongodb.net/"
)
db = client_db["smarthome"]
users_col = db["users"]

# ================= MQTT =================
BROKER = "broker.emqx.io"
PORT = 1883

mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("✅ MQTT Connected:", rc)

mqtt_client.on_connect = on_connect
mqtt_client.connect(BROKER, PORT, 60)
mqtt_client.loop_start()

# ================= LOGIN =================
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

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html", user=session["user"])

# ================= DOOR =================
@app.route("/door/open")
def door_open():
    mqtt_client.publish(
        "namhome/door/cmd",
        json.dumps({"user": session["user"]})
    )
    print("🚪 Web gửi mở cửa")
    return redirect("/dashboard")

# ================= LIGHT =================
@app.route("/light/on")
def light_on():
    mqtt_client.publish(
        "namhome/light/cmd",
        json.dumps({"user": session["user"], "state": "ON"})
    )
    print("💡 Web bật đèn")
    return redirect("/dashboard")

@app.route("/light/off")
def light_off():
    mqtt_client.publish(
        "namhome/light/cmd",
        json.dumps({"user": session["user"], "state": "OFF"})
    )
    print("💡 Web tắt đèn")
    return redirect("/dashboard")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
