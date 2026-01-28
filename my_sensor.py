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
 client_id=f"sensor-{DEVICE_ID}"
)

client.connect(BROKER, PORT)
print(f"Connecté au broker {BROKER}:{PORT}")
compteur = 0


#Intégrez ces métriques dans le message MQTT via la payload.
#Publier toutes les 2 secondes sur pc/sensors/<DEVICE_ID> un JSON contenant :
#• device_id (string)
#• timestamp ISO 8601 (string)
#• metrics (dict) avec au minimum :
#o cpu_usage_percent, memory_usage_percent, disk_usage_percent
#o network_download_kbps, network_upload_kbps
#o disk_read_mbps, disk_write_mbps
#o process_count
#Optionnels : cpu_temperature_c, cpu_frequency_mhz, memory_used_gb,
#memory_total_gb, battery.

cpu_usage = psutil.cpu_percent(interval=0.5)
memory = psutil.virtual_memory()
disk = psutil.disk_usage('/')
    
net_io_before = psutil.net_io_counters()
time.sleep(0.1)
net_io_after = psutil.net_io_counters()

network_download_kbps = (net_io_after.bytes_recv - net_io_before.bytes_recv) * 8 / 100
network_upload_kbps = (net_io_after.bytes_sent - net_io_before.bytes_sent) * 8 / 100
    
disk_io_before = psutil.disk_io_counters()
time.sleep(0.1)
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


while True:
    lire_metriques()
    client.publish(f"pc/sensors/{DEVICE_ID}", json.dumps({
        "device_id": DEVICE_ID,
        "timestamp": datetime.datetime.now().isoformat(),
        "metrics": lire_metriques()
    }))
    print(f"Message publié : {lire_metriques()}")
    time.sleep(10)