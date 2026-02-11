import json
import time
import paho.mqtt.client as mqtt
from pymongo import MongoClient

# ================== MONGODB ==================
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["smarthome"]
users_col = db["users"]
logs_col = db["logs"]

def log_action(user, action):
    logs_col.insert_one({
        "user": user,
        "action": action,
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    })

def get_role(username):
    user = users_col.find_one({"username": username})
    return user["role"] if user else None

# ================== MQTT CONFIG ==================
BROKER = "broker.emqx.io"
PORT = 1883

# ================== CALLBACKS ==================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker")
        client.subscribe("namhome/#")
    else:
        print("❌ Connection failed:", rc)

def on_disconnect(client, userdata, rc):
    print("⚠️ Disconnected! Auto reconnecting...")

def on_message(client, userdata, msg):
    topic = msg.topic

    # ⚠️ CHỐNG CRASH DO SAI JSON
    try:
        data = json.loads(msg.payload.decode())
    except:
        print("⚠️ Bỏ qua message không phải JSON:", msg.payload.decode())
        return

    print("📩", topic, data)

    # ================== MỞ CỬA ==================
    if topic == "namhome/door/cmd":
        user = data.get("user")
        role = get_role(user)

        if role in ["admin", "member"]:
            client.publish("namhome/door/status", json.dumps({"door": "OPEN"}))
            log_action(user, "OPEN DOOR")
        else:
            client.publish("namhome/alarm", "🚨 Unauthorized door access!")
            log_action(user, "FAILED OPEN DOOR")

    # ================== ĐÈN ==================
    elif topic == "namhome/light/cmd":
        user = data.get("user")
        state = data.get("state")
        role = get_role(user)

        if role in ["admin", "member"]:
            client.publish(
                "namhome/light/status",
                json.dumps({"light": state})
            )
            log_action(user, f"LIGHT {state}")

        else:
            client.publish("namhome/system/response", "Permission denied")

    # ================== THÊM USER ==================
    elif topic == "namhome/user/add":
        admin = data.get("admin")
        new_user = data.get("new_user")

        if get_role(admin) == "admin":
            users_col.update_one(
                {"username": new_user},
                {"$set": {"role": "member"}},
                upsert=True
            )
            client.publish("namhome/system/response", f"User {new_user} added")
            log_action(admin, f"ADD USER {new_user}")
        else:
            client.publish("namhome/system/response", "Only admin allowed")

    # ================== XOÁ USER ==================
    elif topic == "namhome/user/delete":
        admin = data.get("admin")
        del_user = data.get("del_user")

        if get_role(admin) == "admin":
            users_col.delete_one({"username": del_user})
            client.publish("namhome/system/response", f"User {del_user} deleted")
            log_action(admin, f"DELETE USER {del_user}")
        else:
            client.publish("namhome/system/response", "Only admin allowed")


# ================== MQTT CLIENT ==================
client = mqtt.Client()

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# ⭐ TỰ ĐỘNG RECONNECT
client.reconnect_delay_set(min_delay=1, max_delay=10)

# Chạy MQTT nền
client.loop_start()

# Kết nối an toàn
while True:
    try:
        print("🔄 Connecting to broker...")
        client.connect(BROKER, PORT, keepalive=60)
        break
    except Exception as e:
        print("❌ MQTT chưa sẵn sàng:", e)
        time.sleep(5)

# Giữ server sống
while True:
    time.sleep(1)
