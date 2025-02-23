from machine import Pin, ADC
import time
import dht
import ujson
import network
from umqtt.simple import MQTTClient
import urequests as requests

# MQTT Server Parameters
MQTT_CLIENT_ID = "esp32-salman"
MQTT_BROKER = "broker.emqx.io"
MQTT_TOPIC = "topic/HSC049/Salman Abdul Aziz/sensor"
MQTT_SUBS_TOPIC = "topic/HSC049/Salman Abdul Aziz/publish_sensor"

# Ubidots API Parameters
DEVICE_ID = "esp32-salman"
UBIDOTS_URL = f"http://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_ID}"
UBIDOTS_HEADERS = {
    "Content-Type": "application/json",
    "X-Auth-Token": "BBUS-kaqYDwiLekdJB6kwlbvHMuiRe7NSFk"
}

# Flask API URL
FLASK_API_URI = "http://192.168.1.10:5000/sensor"

# Pin Setup
led = Pin(4, Pin.OUT)
sensor = dht.DHT11(Pin(5))
ldr = ADC(Pin(34))  
ldr.atten(ADC.ATTN_11DB)

def do_connect():
    """Menghubungkan ke jaringan WiFi."""
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('Menghubungkan ke jaringan WiFi...')
        sta_if.active(True)
        sta_if.connect('SALMA AA', 'azizah21')
        
        timeout = 10
        while not sta_if.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
        
        if not sta_if.isconnected():
            print("Gagal terhubung ke WiFi! Periksa SSID/PASSWORD")
            return False
        
    print('Berhasil terhubung! IP:', sta_if.ifconfig()[0])
    return True

def sub_cb(topic, msg):
    """Callback untuk pesan MQTT."""
    msg = msg.decode('utf-8').strip().lower()
    print("Pesan diterima:", msg)

    if msg == "on":
        led.on()
        print("Lampu dinyalakan")
    elif msg == "off":
        led.off()
        print("Lampu dimatikan")
    else:
        print("Perintah tidak dikenali")

# Hubungkan ke WiFi
if not do_connect():
    print("Coba periksa koneksi WiFi, lalu restart ESP32.")
    while True:
        time.sleep(1)

# Hubungkan ke MQTT
print("Menghubungkan ke MQTT server...")
client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
client.set_callback(sub_cb)
client.connect()
client.subscribe(MQTT_SUBS_TOPIC)
print("Berhasil terhubung ke MQTT!")

while True:
    try:
        client.check_msg()  
        
        # Membaca data dari sensor
        sensor.measure()
        suhu = sensor.temperature()
        kelembaban = sensor.humidity()
        ldr_value = ldr.read()

        # Menampilkan data di terminal
        print(f"Suhu: {suhu}°C, Kelembaban: {kelembaban}%, Cahaya: {ldr_value}")

        # Mengontrol LED berdasarkan suhu
        led.on() if suhu >= 30 else led.off()
        
        # Mengirim data ke MQTT Broker
        message = ujson.dumps({"temp": suhu,
                               "humidity": kelembaban,
                               "light": ldr_value
                               })
        client.publish(MQTT_TOPIC, message)
        
        # Mengirim data ke Ubidots
        ubidots_data = ujson.dumps({"temperature": suhu,
                                    "humidity": kelembaban,
                                    "light": ldr_value
                                    })
        try:
            response = requests.post(UBIDOTS_URL, headers=UBIDOTS_HEADERS, data=ubidots_data, timeout=5)
            print(f"Response Ubidots: {response.status_code}")
            response.close()
        except Exception as e:
            print("Kesalahan saat mengirim data ke Ubidots:", e)
        
        # Mengirim data ke Flask API
        flask_data = ujson.dumps({"temperature": suhu,
                                  "humidity": kelembaban,
                                  "light": ldr_value
                                  })
        try:
            response = requests.post(FLASK_API_URI, headers={"Content-Type": "application/json"}, data=flask_data, timeout=5)
            print(f"Response Flask: {response.status_code}")
            response.close()
        except Exception as e:
            print("Kesalahan saat mengirim data ke Flask API:", e)
        
        time.sleep(1)
        
    except Exception as e:
        print("Error:", e)
        time.sleep(5)
