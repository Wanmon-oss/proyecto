import os
import json
import logging
from dotenv import load_dotenv
import uuid
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
from models import session, TestData

# Carga las variables definidas en el archivo .env (host, usuario, contraseña, etc.)
load_dotenv()

# Lee las variables del entorno o usa valores por defecto si no existen
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER", "admin")
MQTT_PASS = os.getenv("MQTT_PASS", "admin")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "test")

# Configura el sistema de logs para mostrar información en consola
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def on_connect(client, userdata, flags, rc, properties=None):
    """
    Callback que se ejecuta cuando el cliente MQTT logra conectarse al broker.
    rc = código de retorno (0 significa éxito)
    """
    if rc == 0:
        logger.info(f"Conectado al broker MQTT en {MQTT_HOST}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)  # Se suscribe al tópico configurado
        logger.info(f"Suscrito al tópico: {MQTT_TOPIC}")
    else:
        logger.error(f"Error de conexión al broker MQTT (rc={rc})")


def on_message(client, userdata, msg):
    """
    Callback que se ejecuta cada vez que llega un mensaje desde el broker.
    Procesa el JSON recibido y lo guarda en la base de datos si es válido.
    """
    try:
        topic = msg.topic
        payload = msg.payload.decode("utf-8")  # Decodifica bytes → texto

        logger.info(f"Mensaje recibido en '{topic}': {payload[:100]}...")

        # Intenta convertir 
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
        
            data = {"raw": payload}

        # Verifica que existan los campos requeridos
        if "id" in data and "first_name" in data and "last_name" in data:

            # Agrega datos
            data["timestamp"] = datetime.now(ZoneInfo("America/Costa_Rica"))
            data["topic"] = topic

            # Crea un objeto del modelo TestData para almacenar
            record = TestData(
                timestamp=data["timestamp"],
                topic=data["topic"],
                student_id=data["id"],
                first_name=data["first_name"],
                last_name=data["last_name"],
            )

            session.add(record)
            session.commit()  # Guarda definitivamente en la base de datos

            logger.info(f"Registro insertado con ID: {record.id}")

        else:
            logger.warning(f"Datos incompletos recibidos: {data}")

    except Exception as e:
        # Detalladamente cualquier error inesperado
        logger.error(f"Error procesando mensaje: {e}", exc_info=True)


def on_disconnect(client, userdata, flags, rc, properties=None):
    """
    Callback llamado cuando el cliente MQTT se desconecta del broker.
    rc != 0 significa desconexión inesperada.
    """
    if rc != 0:
        logger.warning(f"Desconexión inesperada (rc={rc})")
    else:
        logger.info("Desconectado del broker MQTT correctamente")


def main():
    """Función principal que configura el cliente MQTT y lo ejecuta."""
    logger.info("Iniciando servicio de suscriptor MQTT...")

    # Genera un único para identificar este suscriptor
    client_id = f"subscriber-{uuid.uuid4()}"
    logger.info(f"Cliente MQTT ID: {client_id}")

    # Crea el cliente MQTT 
    client = mqtt.Client(
        client_id=client_id,
        callback_api_version=CallbackAPIVersion.VERSION2
    )

    # Configura usuario y contraseña 
    client.username_pw_set(MQTT_USER, MQTT_PASS)

    # Define tiempos de reconexión automática 
    client.reconnect_delay_set(min_delay=1, max_delay=120)

    # Asigna definidos arriba
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    # Lógica de reintentos
    max_retries = 5
    retry_delay = 5  # segundos

    for attempt in range(max_retries):
        try:
            logger.info(f"Conectando al broker MQTT (intento {attempt+1}/{max_retries})...")
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=120)
            break  # Salimos si la conexión fue exitosa
        except Exception as e:
            logger.warning(f"Intento {attempt+1} fallido: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("No se pudo conectar después de varios intentos")
                return

    # Inicia el loop del cliente: queda escuchando mensajes indefinidamente
    try:
        logger.info("Ejecutando loop MQTT (esperando mensajes)...")
        client.loop_forever()  # Bucle bloqueante
    except KeyboardInterrupt:
        logger.info("Cerrando suscriptor por señal del usuario")
    finally:
        client.disconnect()
        logger.info("Servicio MQTT detenido")


# Ejecuta main() si este archivo se ejecuta directamente
if __name__ == "__main__":
    main()
