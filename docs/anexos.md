```python title="Models"
# Definir los modelos
class TestData(Base):
    """Definición de la tabla de ejemplo."""

    __tablename__ = "test_data"
    id = Column(Integer, primary_key=True) # identificador único
    topic = Column(String)  #Tópico MQTT del que proviene el dato
    timestamp = Column(DateTime) # hora en la que se recibió el dato   
    student_id = Column(String)  # identificador del estudiante
    first_name = Column(String)  # nombre del estudiante
    last_name = Column(String)  # apellido del estudiante


# Crear la conexión a la base de datos SQLite3 o PostgreSQL
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

# Crear la(s) tabla(s) en la base de datos
Base.metadata.create_all(engine)
```
```python title="Client"
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

# Cargar variables de entorno desde archivo .env
load_dotenv()

# Configuraci贸n desde variables de entorno
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER", "admin")
MQTT_PASS = os.getenv("MQTT_PASS", "admin")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "test")

# Configurar logging (registro de eventos en la terminal)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def on_connect(client, userdata, flags, rc, properties=None):
    """Callback (funci贸n de continuaci贸n) para cuando el cliente se conecta al broker"""
    if rc == 0:
        logger.info(f"Conectado al broker MQTT en {MQTT_HOST}:{MQTT_PORT}")  # 馃帀
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Suscrito al t贸pico: {MQTT_TOPIC}")
    else:
        logger.error(f"Fallo al conectar al broker MQTT, c贸digo de retorno: {rc}")


def on_message(client, userdata, msg):
    """Callback para cuando se recibe un mensaje del broker"""
    try:
        topic = msg.topic
        payload = msg.payload.decode("utf-8")

        logger.info(f"Mensaje recibido en el t贸pico '{topic}': {payload[:100]}...")

        # Parsear payload JSON si es aplicable
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = {"raw": payload}

        if "id" in data and "first_name" in data and "last_name" in data:
            # A帽adir metadatos
            data["timestamp"] = datetime.now(ZoneInfo("America/Costa_Rica"))
            data["topic"] = topic

            # Crear registro y guardar en la base de datos
            record = TestData(
                timestamp=data["timestamp"],
                topic=data["topic"],  # T贸pico MQTT del que proviene el dato
                student_id=data["id"],  # identificador del estudiante
                first_name=data["first_name"],  # nombre del estudiante
                last_name=data["last_name"],  # apellido del estudiante
            )
            session.add(record) # guardar en la sesi贸n 
            session.commit()  

            logger.info(f"Datos a帽adidos a la base de datos: {record.id}")
        else:
            logger.warning(f"Datos incompletos recibidos: {data}")

    except Exception as e:
        logger.error(f"Error al procesar mensaje: {e}", exc_info=True)


def on_disconnect(client, userdata, flags, rc, properties=None):
    """Callback para cuando el cliente se desconecta del broker"""
    if rc != 0:
        logger.warning(
            f"Desconexi贸n inesperada del broker MQTT, c贸digo de retorno: {rc}"
        )
    else:
        logger.info("Desconectado del broker MQTT")  


def main():
    """Funci贸n principal para iniciar el suscriptor"""
    logger.info("Iniciando servicio de suscriptor MQTT...")

    # Crear cliente MQTT con callback API v2 y un ID de cliente 煤nico
    client_id = f"subscriber-{uuid.uuid4()}"
    logger.info(f"Usando ID de cliente: {client_id}")
    client = mqtt.Client(
        client_id=client_id, callback_api_version=CallbackAPIVersion.VERSION2
    )
    client.username_pw_set(MQTT_USER, MQTT_PASS)

    # Habilitar reconexi贸n autom谩tica
    client.reconnect_delay_set(min_delay=1, max_delay=120)

    # Configurar callbacks (funciones de continuaci贸n)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    # Conectar al broker MQTT con l贸gica de reintentos
    max_retries = 5
    retry_delay = 5  # segundos

    for attempt in range(max_retries):
        try:
            logger.info(
                f"Intentando conectar al broker MQTT (intento {attempt + 1}/{max_retries})..."
            )
            # Aumentar keepalive a 120 segundos para prevenir desconexiones prematuras
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=120)
            break
        except Exception as e:
            logger.warning(
                f"Intento de conexi贸n MQTT {attempt + 1}/{max_retries} fallido: {e}"
            )
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error(
                    "Fallo al conectar al broker MQTT despu茅s del m谩ximo de reintentos"
                )
                return

    # Iniciar el ciclo de procesamiento de mensajes
    try:
        logger.info("Iniciando ciclo del cliente MQTT...")
        client.loop_forever()  
    except KeyboardInterrupt:
        logger.info("Se帽al de apagado recibida")
    finally:
        client.disconnect()
        logger.info("Servicio de suscriptor detenido")


# Ejecutar la funci贸n principal si este archivo es ejecutado directamente
if __name__ == "__main__":
    main()
```

```python title="Analysis"
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fitter import Fitter, get_common_distributions
from scipy import stats
import os

# Configuración de archivos
DB_PATH = 'test.db'  
IMG_OUTPUT_FIT = 'histograma_ajuste.png' # Nombre para el histograma con ajuste
IMG_OUTPUT_HIST = 'histograma_solo.png' # Nombre para el histograma sin ajuste

def main():
    print("--- Iniciando proceso de Análisis ---")

    # ---------------------------------------------------------
    # 1. Extracción y Transformación (ETL)
    # ---------------------------------------------------------
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encuentra el archivo {DB_PATH}")
        return

    print(f"1. Leyendo datos de {DB_PATH}...")
    
    conn = None
    try:
        # CAMBIO IMPORTANTE:
        # 1. timeout=20: Espera hasta 20 segundos si la DB está ocupada.
        # 2. uri=True y mode=ro: Intenta abrir la base de datos en modo SOLO LECTURA.
        #    Esto reduce la probabilidad de conflictos de bloqueo.
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=20)
    except sqlite3.OperationalError:
        print("    -> Advertencia: Falló modo lectura URI, intentando conexión estándar...")
        try:
            conn = sqlite3.connect(DB_PATH, timeout=20)
        except sqlite3.OperationalError as e:
            print(f"\nCRITICAL ERROR: La base de datos sigue bloqueada.")
            print("Consejo: Si estás accediendo a un archivo de WSL desde Windows Python,")
            print("intenta ejecutar este script usando 'python3' DENTRO de la terminal de WSL.")
            raise e

    # Obtenemos el nombre de la tabla automáticamente
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    if not tables:
        print("Error: No se encontraron tablas en la base de datos.")
        conn.close()
        return
    
    table_name = tables[0][0]
    print(f"    -> Tabla detectada: '{table_name}'")

    # Leemos la tabla en un DataFrame
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()

    # Transformación de Timestamps a Datetime
    time_col = None
    for col in df.columns:
        if 'time' in col.lower() or 'fecha' in col.lower() or 'created' in col.lower():
            time_col = col
            break
    
    if time_col:
        print(f"    -> Columna de tiempo detectada: '{time_col}'")
        df[time_col] = pd.to_datetime(df[time_col])
    else:
        print("Error: No se pudo identificar una columna de timestamp.")
        return

    # ---------------------------------------------------------
    # 2. Obtención de Delays (Ingeniería de Características)
    # ---------------------------------------------------------
    print("2. Calculando delays entre peticiones...")
    
    df = df.sort_values(by=time_col)
    
    # Calculamos la diferencia con la fila anterior
    df['delay_seconds'] = df[time_col].diff().dt.total_seconds()
    
    df_clean = df.dropna(subset=['delay_seconds'])
    df_clean = df_clean[df_clean['delay_seconds'] > 0]
    
    delays = df_clean['delay_seconds'].values
    print(f"    -> Se obtuvieron {len(delays)} muestras de delays válidas.")

    if len(delays) < 2:
        print("Error: No hay suficientes datos para realizar un ajuste estadístico.")
        return

    # ---------------------------------------------------------
    # 3. Visualización y Ajuste Estadístico (Fitter)
    # ---------------------------------------------------------
    print("3. Generando histograma y buscando el mejor ajuste estadístico...")
    
    # Generar histograma SOLO
    plt.figure(figsize=(10, 6))
    plt.hist(delays, bins=50, density=True, alpha=0.6, color='g', label='Datos Reales')
    plt.title('Histograma de Delays')
    plt.xlabel('Delay (segundos)')
    plt.ylabel('Densidad de Probabilidad')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(IMG_OUTPUT_HIST)
    print(f"    -> Gráfico solo de histograma guardado como '{IMG_OUTPUT_HIST}'")
    
    # Generar histograma con ajuste
    plt.figure(figsize=(10, 6))
    
    # Histograma
    plt.hist(delays, bins=50, density=True, alpha=0.6, color='g', label='Datos Reales')

    # Fitter
    f = Fitter(delays, distributions=get_common_distributions(), bins=50) 
    f.fit()
    
    print("    -> Resumen de los mejores ajustes:")
    print(f.summary())
    
    best_dist_name = list(f.get_best(method='sumsquare_error').keys())[0]
    best_params = f.get_best(method='sumsquare_error')[best_dist_name]
    
    print(f"\n    -> MEJOR AJUSTE: Distribución '{best_dist_name}'")
    print(f"    -> Parámetros: {best_params}")

    plt.title(f'Histograma de Delays y Ajuste: {best_dist_name}')
    plt.xlabel('Delay (segundos)')
    plt.ylabel('Densidad de Probabilidad')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(IMG_OUTPUT_FIT)
    print(f"    -> Gráfico con ajuste guardado como '{IMG_OUTPUT_FIT}'")

    # ---------------------------------------------------------
    # 4. Cálculo de Momentos (Datos Reales vs Modelo)
    # ---------------------------------------------------------
    print("\n4. Comparación de Momentos Estadísticos:")
    
    real_mean = np.mean(delays)
    real_var = np.var(delays)
    real_skew = stats.skew(delays)
    real_kurt = stats.kurtosis(delays)

    dist_model = getattr(stats, best_dist_name)
    
    common_params = {k: v for k, v in best_params.items() if k in ['loc', 'scale']}
    shape_params = [v for k, v in best_params.items() if k not in ['loc', 'scale']]
    
    try:
        model_mean, model_var, model_skew, model_kurt = dist_model.stats(*shape_params, **common_params, moments='mvsk')
    except Exception as e:
        print(f"    (No se pudieron calcular momentos teóricos exactos: {e})")
        model_mean, model_var, model_skew, model_kurt = (0, 0, 0, 0)

    comparison_df = pd.DataFrame({
        'Estadístico': ['Media', 'Varianza', 'Asimetría', 'Curtosis'],
        'Datos Reales': [real_mean, real_var, real_skew, real_kurt],
        'Modelo Ajustado': [float(model_mean), float(model_var), float(model_skew), float(model_kurt)]
    })
    
    print("\nResultados Finales:")
    print(comparison_df.to_string(index=False))

    print("\n--- Proceso Finalizado ---")

if __name__ == "__main__":
    main()
```

***Evaluación docente***

![Histograma](images/Evaluacion docente.jpg)