from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os
from dotenv import load_dotenv


# Crear la clase base de la tabla
class Base(DeclarativeBase):
    pass


# Load environment variables from .env file
load_dotenv()

# Datos de configuración
database_url = os.getenv("DATABASE_URL", "sqlite:///test.db")


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
