import time
import json
import socket
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
import psutil

from my_sensor import lire_metriques

BROKER = "10.33.15.158"
PORT = 1883
DEVICE_ID = socket.gethostname()
client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id=f"subscriber-{DEVICE_ID}"
)



client.connect(BROKER, PORT)
print(f"Connecté au broker {BROKER}:{PORT}")


storage = {}

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    device_id = data["device_id"]

    if device_id not in storage:
        storage[device_id] = {
            "metrics": {},
            "timestamp": "",
            "message_count": 0,
            "cpu": 0,
            "download_history": []   
        }

    # maj des données
    storage[device_id]["metrics"] = data["metrics"]
    storage[device_id]["timestamp"] = data["timestamp"]
    storage[device_id]["message_count"] += 1

    # CPU 
    storage[device_id]["cpu"] = data["metrics"].get("cpu_usage_percent", 0)

    # pour le stream 
    download = data["metrics"].get("network_download_kbps", 0)
    storage[device_id]["download_history"].append(download)

    # garder seulement les 10 dernières valeurs
    if len(storage[device_id]["download_history"]) > 10:
        storage[device_id]["download_history"].pop(0)




client.connect(BROKER, PORT)
client.on_message = on_message
client.subscribe("pc/sensors/#")
client.loop_start()



def top3_subscribers():
    # si le storage est vide (donc au lancement)
    if not storage:
        print("j'ai rien recu")
        return
    
    
    #tri le storage par cpu et on prend les 3 premiers
    top3 = sorted(
        storage.items(),
        key=lambda x: x[1].get("cpu", 0),
        reverse=True
    )[:3]
    
    
    print("\n TOP 3 cpu")
    for i, (device_id, data) in enumerate(top3, 1):
        memory = data["metrics"].get("memory_usage_percent", "N/A")
        cpu = data["metrics"].get("cpu_usage_percent", "N/A")
        average = (cpu + memory) / 2
        print(f"{device_id} - moyenne : {average:2f}%")



def probable_streamer():
    best_device = None
    best_avg = 0

    for device_id, data in storage.items():
        history = data["download_history"]

        if len(history) < 3:
            continue  # pas assez de données

        avg_download = sum(history) / len(history)

        if avg_download > best_avg:
            best_avg = avg_download
            best_device = device_id

    if best_device and best_avg > 2000:
        print(
            f"\nstreamer : {best_device} "
            f"(moyenne : {round(best_avg, 2)} kbps)"
        )
    else:
        print("\nAucun streamer détecté, sad")

   


while True:
    

    top3_subscribers()
    probable_streamer()

    time.sleep(5)
