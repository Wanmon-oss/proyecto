### Ejecución del Proyecto

La ejecución del proyecto se divide en dos fases principales: la recolección de datos mediante el cliente MQTT y el análisis estadístico de los tiempos entre eventos consecutivos. A continuación se describe detalladamente el funcionamiento de cada parte del sistema y cómo se integran para cumplir con los objetivos planteados.

***1-Recolección de datos (client.py)***

El proceso inicia con la ejecución del script encargado de conectarse al intermediador MQTT proporcionado por SIMOVI. Este cliente establece una conexión con el broker público ubicado en tcp://mqtt.simovi.org:1883 y se suscribe al tópico correspondiente al carné universitario del estudiante.

Una vez establecida la conexión, el programa queda en modo de escucha permanente, recibiendo los mensajes publicados en ese tópico. Cada mensaje contiene un registro temporal (timestamp) asociado a un evento. Al recibir un mensaje, el cliente extrae dicho valor, lo transforma al formato adecuado y lo almacena en la base de datos mediante el modelo definido en models.py.

Este proceso se mantiene activo durante varias horas continuas, permitiendo acumular una cantidad suficiente de datos que represente el comportamiento natural del sistema. Cada evento recibido queda registrado de manera ordenada y persistente, sirviendo como base para el análisis posterior.

***2-Procesamiento y análisis de datos (analysis.py)***

Una vez finalizada la etapa de recolección, se procede a la ejecución del módulo de análisis. Este script se encarga de cargar todos los eventos almacenados en la base de datos y ordenarlos cronológicamente. Con esta secuencia temporal, se calculan las diferencias en segundos entre cada par de eventos consecutivos, generando así el conjunto de tiempos inter-arribo que constituyen la variable principal del estudio.

Con esta información, se realiza un análisis exploratorio que incluye la generación de histogramas y otras representaciones gráficas que permiten visualizar la distribución empírica de los datos. Posteriormente, se calculan los momentos estadísticos relevantes: media, varianza, desviación estándar, inclinación y curtosis, con el fin de describir cuantitativamente el comportamiento de la variable analizada.

Finalmente, se aplican métodos de ajuste de distribuciones utilizando herramientas especializadas que permiten identificar cuál modelo probabilístico se ajusta mejor a los datos observados. Este procedimiento permite proponer una distribución estadística adecuada junto con sus parámetros y compararla con el histograma de los valores reales.

***3- Resultado global del proceso***

El proyecto culmina con la integración de ambas etapas: la captura en tiempo real de los eventos mediante MQTT y el análisis estadístico profundo de los tiempos inter-arribo. Como resultado, se obtiene una caracterización completa del sistema mediante visualizaciones, momentos estadísticos y un modelo de probabilidad capaz de describir adecuadamente la dinámica temporal de los eventos registrados.