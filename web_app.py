from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import datetime
import os

app = Flask(__name__)
CORS(app)

# ===== MongoDB Atlas =====
MONGO_URI = os.getenv("MONGO_URI")  # set trong Render Environment
client = MongoClient(MONGO_URI)
db = client["smarthome"]
logs_collection = db["logs"]

# ==========================
@app.route("/")
def home():
    return "Server is running!"

# ===== API MỞ CỬA =====
@app.route("/open_door", methods=["POST"])
def open_door():
    print(">> OPEN DOOR pressed")

    logs_collection.insert_one({
        "action": "open_door",
        "time": datetime.datetime.utcnow()
    })

    return jsonify({"status": "Door opened"})


# ===== API BẬT ĐÈN =====
@app.route("/light_on", methods=["POST"])
def light_on():
    print(">> LIGHT ON pressed")

    logs_collection.insert_one({
        "action": "light_on",
        "time": datetime.datetime.utcnow()
    })

    return jsonify({"status": "Light ON"})


# ===== API TẮT ĐÈN =====
@app.route("/light_off", methods=["POST"])
def light_off():
    print(">> LIGHT OFF pressed")

    logs_collection.insert_one({
        "action": "light_off",
        "time": datetime.datetime.utcnow()
    })

    return jsonify({"status": "Light OFF"})


# ===== LẤY LOG =====
@app.route("/logs", methods=["GET"])
def get_logs():
    logs = list(logs_collection.find({}, {"_id": 0}))
    return jsonify(logs)


# ===== PORT Render =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
