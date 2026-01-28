import time
import json
import socket
import paho.mqtt.client as mqtt
import datetime
import psutil

BROKER = "10.33.15.158"
PORT = 1883
DEVICE_ID = socket.gethostname()
client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id=f"subscriber-{DEVICE_ID}"
)



client.connect(BROKER, PORT)
print(f"Connecté au broker {BROKER}:{PORT}")


#####################################################
# 5. Capteur réel : métriques système
#####################################################

# création de toutes la variables pour les rentrées dans les métrics 
cpu_usage = psutil.cpu_percent(interval=0.5)
memory = psutil.virtual_memory()
disk = psutil.disk_usage('/')
net_io_before = psutil.net_io_counters()
net_io_after = psutil.net_io_counters()
network_download_kbps = (net_io_after.bytes_recv - net_io_before.bytes_recv) * 8 / 100
network_upload_kbps = (net_io_after.bytes_sent - net_io_before.bytes_sent) * 8 / 100
disk_io_before = psutil.disk_io_counters()
disk_io_after = psutil.disk_io_counters()
disk_read_mbps = (disk_io_after.read_bytes - disk_io_before.read_bytes) / 100 / 1024 / 1024
disk_write_mbps = (disk_io_after.write_bytes - disk_io_before.write_bytes) / 100 / 1024 / 1024
process_count = len(psutil.pids())

def lire_metriques():
    metrics = {
        "cpu_usage_percent": round(cpu_usage, 2),
        "memory_usage_percent": round(memory.percent, 2),
        "disk_usage_percent": round(disk.percent, 2),
        "network_download_kbps": round(network_download_kbps, 2),
        "network_upload_kbps": round(network_upload_kbps, 2),
        "disk_read_mbps": round(disk_read_mbps, 4),
        "disk_write_mbps": round(disk_write_mbps, 4),
        "process_count": process_count,
}
    return metrics

#####################################################
# 6. Subscriber : réception et traitement
#####################################################

storage = {}

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    device_id = data["device_id"]

    if device_id not in storage:
        storage[device_id] = {
            "metrics": {},
            "timestamp": "",
            "message_count": 0
        }
    # on met les données dans le storage correspondant au device_id
    storage[device_id]["metrics"] = data["metrics"]
    storage[device_id]["timestamp"] = data["timestamp"]
    storage[device_id]["message_count"] += 1



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
        key=lambda x: x[1]["metrics"].get("cpu_usage_percent", 0),
        reverse=True
    )[:3]

    print("\n TOP 3 cpu")
    for i, (device_id, data) in enumerate(top3, 1):
        cpu = data["metrics"].get("cpu_usage_percent", "N/A")
        print(f"{device_id} - CPU : {cpu}%")

        
#####################################################


while True:
    
    # client.publish(f"pc/sensors/{DEVICE_ID}", json.dumps({
    #     "device_id": DEVICE_ID,
    #     "timestamp": datetime.datetime.now().isoformat(),
    #     "metrics": lire_metriques()
    # }))
    # print(lire_metriques())
    
    client.publish(
        f"pc/sensors/{DEVICE_ID}",
        json.dumps({
            "device_id": DEVICE_ID,
            "timestamp": datetime.datetime.now().isoformat(),
            "metrics": lire_metriques()
        })
    )

    top3_subscribers()
    time.sleep(2)
