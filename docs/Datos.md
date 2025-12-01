### Recolección de datos 

En esta parte, se procedió a recolectar la información necesaria para realizar los procesos estadisticos. Para esto, se baso en los documentos dados de la carpeta. 

Es importante destacar la función de densidad de probabilidad se define como:

$$
f(\Delta t; \lambda) = \lambda e^{-\lambda \Delta t}
$$

Con los datos del proyecto se obtiene que nuestra función corresponde a: 

$$
f(\Delta t) = 0.0308 \, e^{-0.0308 \, \Delta t}
$$


## Descripción de partes importantes del código
 
 - *Carga y conexión a la base de datos (ETL)*

El script comienza leyendo la base de datos SQLite donde están almacenados los registros de tiempo. Para evitar bloqueos o errores, la conexión se intenta primero en modo de solo lectura:

```python title="Python"
for col in df.columns:
    if 'time' in col.lower() or 'fecha' in col.lower() or 'created' in col.lower():
        time_col = col
```

Esto permite:

Acceder a la base sin modificarla, seguidamente se detecta la tabla de manera automática:

  cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")


Finalmente, la tabla se carga en un DataFrame de pandas:

```python title="Python"
  df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
```


- *Identificación automática de la columna de tiempo*

Para no depender del nombre exacto de la columna con timestamps, el código la detecta buscando palabras comunes:

```python title="Python"
for col in df.columns:
    if 'time' in col.lower() or 'fecha' in col.lower() or 'created' in col.lower():
        time_col = col
```



Después convierte esa columna al formato datetime:

```python title="Python"
 df[time_col] = pd.to_datetime(df[time_col])
```



Esto estandariza los datos y permite calcular delays correctamente.

- *Cálculo de los delays entre eventos*

Primero, los datos se ordenan temporalmente:

```python title="Python"
 df = df.sort_values(by=time_col)
```



Luego se calcula la diferencia de tiempo entre una fila y la siguiente:

```python title="Python"
 df['delay_seconds'] = df[time_col].diff().dt.total_seconds()
```



Después se limpian los datos:

```python title="Python"
 df_clean = df.dropna(subset=['delay_seconds'])
 df_clean = df_clean[df_clean['delay_seconds'] > 0]

```


El vector final de delays queda en:

```python title="Python"
 delays = df_clean['delay_seconds'].values
```


### Histograma de los datos 

A continuación, se muestra el histograma con los datos reales

![Histograma](images/histograma_solo.png)