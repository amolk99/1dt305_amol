import network
import time
from simple import MQTTClient
import machine
import onewire
import ds18x20
import dht

# wifi credentials
SSID = 'Telia-3611E0'
PASSWORD = 'y7rhZucZrNhT6FfF'

# Thingspeak MQTT settings
MQTT_CLIENT_ID = 'NQ4aBjA7EREfNDAxBA8zHQI'
MQTT_USERNAME = 'NQ4aBjA7EREfNDAxBA8zHQI'
MQTT_PASSWORD = '6VMBrM0wxAWM+LOWoNtLQySX'
MQTT_SERVER = 'mqtt3.thingspeak.com'
MQTT_PORT = 1883
CHANNEL_ID = '2583390'
WRITE_API_KEY = 'BWN7HUVG4JTMM2Y6'

# init DS18B20
ds_pin = machine.Pin(16)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

# init onboard led
led = machine.Pin('LED', machine.Pin.OUT)
# init external led
status_led = machine.Pin(14, machine.Pin.OUT)

# init DHT11 sensor
dht_sensor = dht.DHT11(machine.Pin(15))

# to blink the led
def blink_led(pin, times, interval):
    for x in range(times):
        pin.value(1)
        time.sleep(interval)
        pin.value(0)
        time.sleep(interval)

# to connect to wifi
def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    while not wlan.isconnected():
        print("Connecting to wifi...")
        blink_led(led, 1, 0.2)  # Blink rapidly
        time.sleep(1)
    
    print("Connected to wifi")
    led.value(1)  # Turn led on solid
    time.sleep(2)  # led on for 2 seconds
    led.value(0)  # Turn led off

def read_temperature():
    try:
        roms = ds_sensor.scan()
        if not roms:
            raise Exception("No DS18B20 sensors found")
        ds_sensor.convert_temp()
        time.sleep_ms(750)
        for rom in roms:
            temp = ds_sensor.read_temp(rom)
            return temp
    except Exception as e:
        print(f"Error reading temperature: {e}")
        blink_led(status_led, 5, 0.2)  # Blink rapidly for error indication
        return None

def read_dht11():
    try:
        dht_sensor.measure()
        return dht_sensor.temperature(), dht_sensor.humidity()
    except OSError as e:
        print('Failed to read DHT11 sensor.')
        return None, None

# this is used to approximate the heat index of the apartment 
def calculate_heat_index(T, RH):
    c1 = -8.78469475556
    c2 = 1.61139411
    c3 = 2.33854883889
    c4 = -0.14611605
    c5 = -0.012308094
    c6 = -0.0164248277778
    c7 = 0.002211732
    c8 = 0.00072546
    c9 = -0.000003582

    HI = (c1 + (c2 * T) + (c3 * RH) + (c4 * T * RH) + 
          (c5 * T**2) + (c6 * RH**2) + (c7 * T**2 * RH) + 
          (c8 * T * RH**2) + (c9 * T**2 * RH**2))
    return HI

def mqtt_connect():
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_SERVER, port=MQTT_PORT, user=MQTT_USERNAME, password=MQTT_PASSWORD, keepalive=60)
    client.connect()
    print("Connected to MQTT Broker")
    return client

def send_to_thingspeak(client, temp, humidity, heat_index):
    try:
        topic = f'channels/{CHANNEL_ID}/publish'
        payload = f'field1={temp}&field2={humidity}&field3={heat_index}&status=MQTTPUBLISH'
        blink_led(status_led, 2, 0.5)  # Blink slowly
        client.publish(topic, payload)
        print(f"Data sent to ThingSpeak: Temperature={temp}, Humidity={humidity}, Heat Index={heat_index}")
        status_led.value(1)  # Turn led on solid
        time.sleep(1)  # led on for 1 second
        status_led.value(0)  # Turn led off
    except Exception as e:
        print(f"Failed to send data: {e}")
        # Blink rapidly for failure
        blink_led(status_led, 5, 0.2)
        # Attempt to reconnect
        client.disconnect()
        client.connect()

# Main program
connect_to_wifi()
client = mqtt_connect()

while True:
    temp_ds = read_temperature()
    temp_dht, humidity_dht = read_dht11()
    
    # Check if both sensors returned valid values
    if temp_ds is not None and temp_dht is not None and humidity_dht is not None:
        print(f"DS18B20 Temperature: {temp_ds}")
        print(f"DHT11 Temperature: {temp_dht}, Humidity: {humidity_dht}")
        heat_index = calculate_heat_index(temp_dht, humidity_dht)
        print(f"Heat Index: {heat_index}")
        send_to_thingspeak(client, temp_ds, humidity_dht, heat_index)
    else:
        print("Failed to read from one or both sensors.")
    
    time.sleep(15)  # ThingSpeak allows updates every 15 seconds
