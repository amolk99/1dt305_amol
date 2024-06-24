import network
import time
from simple import MQTTClient
import machine

# WiFi credentials
SSID = 'Telia-3611E0'
PASSWORD = 'y7rhZucZrNhT6FfF'

# ThingSpeak MQTT settings
MQTT_CLIENT_ID = 'NQ4aBjA7EREfNDAxBA8zHQI'
MQTT_USERNAME = 'NQ4aBjA7EREfNDAxBA8zHQI'
MQTT_PASSWORD = '6VMBrM0wxAWM+LOWoNtLQySX'
MQTT_SERVER = 'mqtt3.thingspeak.com'
MQTT_PORT = 1883
CHANNEL_ID = '2583390'
WRITE_API_KEY = 'BWN7HUVG4JTMM2Y6'

# Initialize ADC
adc = machine.ADC(27)
sf = 4095 / 65535  # Scale factor
volt_per_adc = (3.3 / 4095)

# Function to connect to WiFi
def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    while not wlan.isconnected():
        print("Connecting to WiFi...")
        time.sleep(1)
    
    print("Connected to WiFi")

def read_temperature():
    millivolts = adc.read_u16()
    adc_12b = millivolts * sf
    volt = adc_12b * volt_per_adc

    # MCP9700 characteristics
    dx = abs(50 - 0)
    dy = abs(0 - 0.5)
    shift = volt - 0.5
    temp = shift / (dy / dx)
    return temp

def mqtt_connect():
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_SERVER, port=MQTT_PORT, user=MQTT_USERNAME, password=MQTT_PASSWORD)
    client.connect()
    print("Connected to MQTT Broker")
    return client

def send_to_thingspeak(client, temp):
    try:
        topic = f'channels/{CHANNEL_ID}/publish'
        payload = f'field1={temp}&status=MQTTPUBLISH'
        client.publish(topic, payload)
        print(f"Data sent to ThingSpeak: {temp}")
    except Exception as e:
        print(f"Failed to send data: {e}")

# Main program
connect_to_wifi()
client = mqtt_connect()

while True:
    temp = read_temperature()
    print(f"Temperature: {temp}")
    send_to_thingspeak(client, temp)
    time.sleep(15)  # ThingSpeak allows updates every 15 seconds
