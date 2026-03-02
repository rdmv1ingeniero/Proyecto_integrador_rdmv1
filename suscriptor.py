import paho.mqtt.client as mqtt
import mysql.connector

BROKER = "test.mosquitto.org"
PORT = 1883
#USER = "itt363-grupo3"
#CLAVE = "CnFebqnjbq7F"
TOPIC_GENERAL = "/itt363-grupo3/estacion-1/sensores/#"

try:
    db = mysql.connector.connect(
        host="localhost",
        user="itt363",
        password="9Xd%2@DpEdWH!M@",
        database="estacion_meteorologica"
    )
    cursor = db.cursor()
    print("conectado a mysql")
except Exception as e:
    print("error al conectarse a mysql:",e)


def on_connect(client, userdata, flags, rc):
    print("Código de resultado:", rc)
    if rc == 0:
        print(f"Suscriptor conectado escuchando en {TOPIC_GENERAL}...")
        client.subscribe(TOPIC_GENERAL)
    else:   
        print(f"Error de conexion")


def on_message(client, userdata, msg):
    try:
        print("Topic recibido:", msg.topic)

        partes = msg.topic.strip("/").split("/")

        if len(partes) >= 4:
            estacion = partes[1]
            sensor = partes[3]
        else:
            print("Topic inválido:", msg.topic)
            return

        valor = float(msg.payload.decode())

        print(f"Insertando -> Estacion: {estacion}, Sensor: {sensor}, Valor: {valor}")

        sql = """
        INSERT INTO lecturas (estacion, sensor, valor)
        VALUES (%s, %s, %s)
        """

        cursor.execute(sql, (estacion, sensor, valor))
        db.commit()

        print("Datos guardados correctamente")

    except Exception as e:
        print("Error guardando en la base de datos :", e)

        
client = mqtt.Client()
#client.username_pw_set(USER, CLAVE)
client.on_connect = on_connect
client.on_message = on_message

print("conectando a broker")
client.connect(BROKER, PORT)

client.loop_forever()