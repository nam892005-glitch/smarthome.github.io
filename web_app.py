from flask import Flask, render_template, request, redirect, session, jsonify
from pymongo import MongoClient
import paho.mqtt.client as mqtt
import json, os, datetime

app = Flask(__name__)
app.secret_key = "smarthome_secret"

MONGO_URI = "mongodb+srv://smarthome_user:123@cluster0.3s47ygi.mongodb.net/"
mongo = MongoClient(MONGO_URI)
db = mongo["smarthome"]
users_col = db["users"]
logs_col = db["logs"]

BROKER="broker.emqx.io"
mqtt_client = mqtt.Client()

last_status={}

def on_connect(c,u,f,rc):
    c.subscribe("smarthome/+/status")

def on_message(c,u,msg):
    global last_status
    last_status=json.loads(msg.payload.decode())

mqtt_client.on_connect=on_connect
mqtt_client.on_message=on_message
mqtt_client.connect(BROKER,1883,60)
mqtt_client.loop_start()

# LOGIN
@app.route("/",methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form["username"]
        p=request.form["password"]
        user=users_col.find_one({"username":u,"password":p})
        if user:
            session["user"]=u
            session["role"]=user["role"]
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/dashboard")
def dash():
    if "user" not in session: return redirect("/")
    return render_template("dashboard.html",user=session["user"],role=session["role"])

# CONTROL
@app.route("/door",methods=["POST"])
def door():
    mqtt_client.publish("smarthome/door/cmd",json.dumps({"user":session["user"]}))
    return "OK"

@app.route("/light",methods=["POST"])
def light():
    state=request.form["state"]
    mqtt_client.publish("smarthome/light/cmd",
                        json.dumps({"user":session["user"],"state":state}))
    return "OK"

@app.route("/status")
def status():
    return last_status

@app.route("/logs")
def logs():
    return jsonify(list(logs_col.find({},{"_id":0}).sort("time",-1).limit(20)))

# ADMIN USER MANAGEMENT
@app.route("/users")
def users():
    if session["role"]!="admin": return "No permission"
    return render_template("users.html",users=list(users_col.find()))

@app.route("/add_user",methods=["POST"])
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

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
