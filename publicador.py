import paho.mqtt.client as mqtt
import random
import time
import json

BROKER = "test.mosquitto.org"
PORT = 1883
USER = "itt363-grupo3"
CLAVE = "CnFebqnjbq7F"

ESTACIONES = ["estacion-1"]


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Publicador conectado")
    else:
        print(f"error de conexion")



def generar_datos():
    return {
        "temperatura": round(random.uniform(20, 35), 2),
        "humedad": round(random.uniform(40, 90), 2),
        "presion": round(random.uniform(950, 1050), 2),
        "viento": round(random.uniform(0, 20), 2),
        "lluvia": round(random.uniform(0, 10), 2),
    }


client = mqtt.Client()
#client.username_pw_set(USER, CLAVE)
client.on_connect = on_connect

print(f"Conectando a {BROKER}...")
client.connect(BROKER, PORT)
client.loop_start()

try:
    while True:
        for id_estacion in ESTACIONES:
            datos = generar_datos()
            base_topic = f"/itt363-grupo3/{id_estacion}/sensores"
            
            print(f"===Enviando datos de {id_estacion}===")
            for sensor, valor in datos.items():
                topic = f"{base_topic}/{sensor}"
                client.publish(topic, valor)
                print(f"Publicado: {topic} > {valor}")
        
        time.sleep(5) 


#ctrl+c
except KeyboardInterrupt:
    print("terminado") 
finally:
    client.loop_stop()
    client.disconnect()