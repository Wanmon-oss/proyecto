# Proyecto de programación de IE0405 - Modelos Probabilísticos de Señales y Sistemas

### Estudiante: Wanda Monge Guido C24945"


Componentes del Proyecto
*** Suscriptor MQTT (subscriber.py)***

* Se conecta al broker MQTT usando credenciales definidas en .env.

* Recibe mensajes con formato JSON.

* Inserta los datos en la base de datos test.db.

* Incluye manejo de errores, reconexión automática y logs.

***2. Base de Datos SQLite (test.db)***

Guarda el ID, nombre, apellido, timestamp y tópico de cada mensaje recibido.

Es consultada posteriormente por el módulo de análisis.

***3. Analizador Estadístico (analisis.py)***

Este script:

* Extrae la tabla desde test.db.

* Convierte los timestamps.

* Calcula el delay entre mensajes consecutivos.

* Limpia datos inválidos.

* Genera dos figuras


* Compara momentos estadísticos reales vs modelo ajustado.



## Documentación e instrucciones del proyecto

Las instrucciones del proyecto están disponibles en la página:

[https://mpss-eie.github.io/proyecto](https://mpss-eie.github.io/proyecto)

## Instrucciones para ejecución local

Algunos de los paquetes y funcionalidades del proyecto solamente corren en los sistemas operativos tipo Unix, como Linux y macOS.

Por esta razón, las personas con Windows deben utilizar el WSL (*Windows Subsystem for Linux*) de Microsoft (o solución equivalente).

### Windows

Las [instrucciones de instalación](https://learn.microsoft.com/es-mx/windows/wsl/install) indican que solamente es necesario la siguiente instrucción en la terminal, la cual instala la distribución Ubuntu, por defecto:

```bash
wsl --install
```

Una vez en la terminal (o consola o interfaz de línea de comandos) en Linux en WSL, es necesario tener un usuario con privilegios `sudo`. Es posible configurarlo con:

```bash
adduser <username>
```

donde `<username>` puede ser, por ejemplo, `bayes` o `laplace` o `markov` o un nombre de su preferencia (`funkytomato`), y luego ingresar

```bash
usermod -aG sudo <username>
```

para actualizar los permisos. Para cambiar de usuario `root` a `<username>` y empezar una nueva sesión de terminal con ese usuario, utilizar

```bash
su <username>
```

### Clonar el repositorio

Para comenzar, es necesario "clonar" el repositorio con sus archivos localmente. Para esto:

- Asegurarse de que Git está instalado. Es posible verificar con `$ git --version`.
- Ubicarse en el directorio donde estará ubicado el proyecto, con `$ cd [PATH]`.
- Clonar el proyecto con `$ git clone https://github.com/mpss-eie/proyecto.git`.
- Moverse al directorio del proyecto con `$ cd proyecto/`.
- Si no fue hecho antes, configurar las credenciales de Git en el sistema local, con `$ git config --global user.name "Nombre Apellido"` y `$ git config --global user.email "your-email@example.com"`, de modo que quede vinculado con la cuenta de GitHub.


### Crear un ambiente virtual de Python con `uv`

En una terminal, en el directorio raíz del repositorio, utilizar:

```bash
uv sync
```

Esto creará un ambiente virtual (directorio `.venv/`) e instalará las dependencias indicadas en `pyproject.toml`.

#### Instalación o remoción de paquetes

Para ser ejecutado correctamente, cada vez que un paquete nuevo sea utilizado debe ser agregado con `uv` al ambiente virtual usando:

```sh
uv add nombre-del-paquete
```

y para eliminarlo:

```sh
uv remove nombre-del-paquete
```


### Para ejecutar el proyecto

1. Copiar los contenidos del archivo `.env.example` en otro archivo `.env` y modificar los valores necesarios.
1. En el directorio raíz, ejecutar:

```sh
uv run src/client.py
```


