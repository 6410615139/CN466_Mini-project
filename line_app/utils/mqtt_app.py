import paho.mqtt.client as mqttc
import time
import json
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

# constants
MQTT_BROKER = os.environ["MQTT_BROKER"]
MQTT_PORT = int(os.environ["MQTT_PORT"])

MQTT_SUB_TOPIC = "TU/TSE/CN466/supakrit/loopback"
MQTT_PUB_TOPIC = "TU/TSE/CN466/supakrit/loopback"
# loopback - pub and sub are the same person

SQL_CMD_CREATE_TABLE = '''CREATE TABLE IF NOT EXISTS sensor_db (
    _id INTEGER PRIMARY KEY AUTOINCREMENT, 
    tstamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
    value REAL)
'''
SQL_CMD_QUERY_DATA = '''SELECT * FROM sensor_db ORDER BY tstamp DESC LIMIT ''' 
SQL_CMD_INSERT_DATA = '''INSERT INTO sensor_db (value) VALUES (?)'''
SQL_CMD_UPDATE_LAST_DATA = '''UPDATE sensor_db SET value = ? WHERE tstamp = (SELECT MAX(tstamp) FROM sensor_db)'''

# connect MQTT
def connect_mqtt():
    def on_connect(client, userdata, flags, rc, properties):
        if rc == 0:
            print("Connected to MQTT Broker!")
            client.subscribe(MQTT_SUB_TOPIC)
        else:
            print("Failed to connect, return code %d\n", rc)
        
    def on_message(client, userdata, msg):
        topic = msg.topic
        payload = json.loads(msg.payload.decode('utf-8'))
        print(topic, payload)
        if payload["container"] != os.environ["DOCKER"]:
            return
        if payload["command"] == "CREATE":
            dbase_insert(payload["value"])
        elif payload["command"] == "READ":
            rows = dbase_query()
            print(rows)
        else:
            print("Unknown command")
        
    # init MQTT client
    client = mqttc.Client(mqttc.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT)
    return client

# handle SQLite init table
def dbase_init(): 
    conn = sqlite3.connect(os.environ["DB_NAME"])
    cursor = conn.cursor()
    cursor.execute(SQL_CMD_CREATE_TABLE)
    conn.commit()
    conn.close()

# handle SQLite insert data
def dbase_insert(value):
    conn = sqlite3.connect(os.environ["DB_NAME"])
    cursor = conn.cursor()
    cursor.execute(SQL_CMD_INSERT_DATA, (value,))
    conn.commit()
    conn.close()

# handle SQLite query data
def dbase_query():
    conn = sqlite3.connect(os.environ["DB_NAME"])
    cursor = conn.cursor()
    cursor.execute(SQL_CMD_QUERY_DATA)
    rows = cursor.fetchall()
    conn.close()
    return rows

# prepare SQLite
dbase_init()
# prepare MQTT
# mqttClient = connect_mqtt()
# count = 0
# while True:
#     time.sleep(3)
#     payload = {"container":os.environ["DOCKER"], "command":"CREATE", "value":count}
#     mqttClient.publish(MQTT_PUB_TOPIC, json.dumps(payload))
#     count += 1
#     mqttClient.loop()