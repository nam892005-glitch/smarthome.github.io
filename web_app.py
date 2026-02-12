from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt
import json
import os
import time

app = Flask(__name__)

# ===== MQTT CONFIG =====
BROKER = "broker.emqx.io"
PORT = 1883
TOPIC_CMD = "namhome/door/cmd"
TOPIC_STATUS = "namhome/door/status"

# ===== MQTT CALLBACKS =====
def on_connect(client, userdata, flags, rc):
    print("✅ MQTT Connected with result code", rc)
    client.subscribe("namhome/#")
    print("📡 Subscribed to namhome/#")

def on_message(client, userdata, msg):
    print(f"📩 RAW: {msg.topic} {msg.payload.decode()}")
    if msg.topic == TOPIC_STATUS:
        print("🚪 Door status:", msg.payload.decode())

def on_disconnect(client, userdata, rc):
    print("❌ MQTT Disconnected. Reconnecting...")
    while True:
        try:
            client.reconnect()
            print("🔁 Reconnected MQTT")
            break
        except:
            time.sleep(5)

# ===== CREATE MQTT CLIENT =====
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.on_disconnect = on_disconnect

mqtt_client.connect(BROKER, PORT, 60)
mqtt_client.loop_start()   # 🔥 QUAN TRỌNG: chạy nền

print("🚀 MQTT background thread started")

# ===== WEB ROUTES =====
@app.route("/")
def home():
    return "Smart Home Server Running 🚀"

@app.route("/open", methods=["POST"])
def open_door():
    data = {
        "user": "nam",
        "action": "open"
    }
    mqtt_client.publish(TOPIC_CMD, json.dumps(data))
    print("📤 Sent OPEN command")
    return jsonify({"status": "sent open"})

@app.route("/close", methods=["POST"])
def close_door():
    data = {
        "user": "nam",
        "action": "close"
    }
    mqtt_client.publish(TOPIC_CMD, json.dumps(data))
    print("📤 Sent CLOSE command")
    return jsonify({"status": "sent close"})
