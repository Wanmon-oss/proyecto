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