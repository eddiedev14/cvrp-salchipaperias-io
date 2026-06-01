import os
from dotenv import load_dotenv

load_dotenv();

# ============================
# ETAPA 1: Instalación e importación de librerías
# ============================

# ============================
# Importación de librerías
# ============================

import pandas as pd
from sklearn.cluster import KMeans          # Algoritmo K-Means para clustering
import requests                             # Consultar la API Distance Matrix de Google Maps y CSV de Github
from ortools.linear_solver import pywraplp  # Programación Lineal Entera y Mixta (MILP) para CVRP
import random                               # Generar números aleatorios
import csv                                  # Manejo de CSV
from math import radians, cos               # Cálculos matemáticos con radianes
import numpy as np                          # Manejo de matrices
import time

# Graficacion (Mapas interactivos con OpenStreetMap)
import folium
from folium.plugins import BeautifyIcon
from shapely.geometry import MultiPoint

# Envío de Emails
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

print("Etapa 1 completada: librerías instaladas e importadas correctamente.")

# ================================================
# ETAPA 2: Carga del CSV desde GitHub y demandas aleatorias
# ================================================

# URL cruda del archivo en GitHub
url = "https://raw.githubusercontent.com/eddiedev14/CVRP-Salchipaperias-IO/refs/heads/main/salchipaperias.csv"

# Descargar archivo temporalmente usando requests
response = requests.get(url)
response.raise_for_status()  # Asegura que la descarga fue exitosa
with open("salchipaperias.csv", "wb") as f:
    f.write(response.content)

salchipaperias = []  # almacenará cada fila del CSV con su respectiva demanda

# Abrir y leer el CSV
with open("salchipaperias.csv", "r", encoding="utf-8") as f:
    lector = csv.reader(f)

    next(lector)  # saltar encabezado si existe

    for fila in lector:
        demanda = round(random.uniform(100, 500), 2) # Demanda aleatoria por cada nodo de entre 100 kg y 500 kg

        salchipaperias.append({
            "id": fila[0],
            "nombre": fila[1],
            "direccion": fila[2],
            "lat": float(fila[3]),
            "lon": float(fila[4]),
            "demanda": demanda
        })

# Imprimir todas las salchipaperías con su demanda asignada
print("=== LISTA DE SALCHIPAPERÍAS CON DEMANDA ASIGNADA ===\n")
for i, s in enumerate(salchipaperias):
    print(f"ID: {s['id']}")
    print(f"Nombre: {s['nombre']}")
    print(f"Dirección: {s['direccion']}")
    print(f"Coordenadas (lat, lon): ({s['lat']}, {s['lon']})")
    print(f"Demanda asignada: {s['demanda']} kg")
    print("-" * 50)

# ============================================
# ETAPA 3: Proyección a KM y algoritmo K-MEANS
# ============================================

# Lista donde se guardarán las coordenadas proyectadas en km
puntos_km = []

# Tomamos una latitud media para mejorar la precisión de la proyección
latitudes = [float(s["lat"]) for s in salchipaperias]
lat_media = sum(latitudes) / len(latitudes)
lat_media_rad = radians(lat_media)

# Convertir lat/lon a coordenadas en km
for s in salchipaperias:
    lat_rad = radians(s["lat"])
    lon_rad = radians(s["lon"])

    # Fórmula equirectangular (distancias aproximadas en km)
    x = (lon_rad - radians(salchipaperias[0]["lon"])) * cos(lat_media_rad) * 6371
    y = (lat_rad - radians(salchipaperias[0]["lat"])) * 6371

    puntos_km.append([x, y])

# Aplicar K-Means con 3 clusters
kmeans = KMeans(n_clusters=3, random_state=0)
kmeans.fit(puntos_km)

# Asignar cluster a cada salchipapería
for i, s in enumerate(salchipaperias):
    s["cluster"] = int(kmeans.labels_[i])

# Imprimir resultado de clusters
print("=== AGRUPACIÓN K-MEANS ===\n")
for s in salchipaperias:
    print(f"ID {s['id']} | {s['nombre']} -> Cluster {s['cluster']}")

# ============================================
# ETAPA 4: MAPA FOLIUM DE TODOS LOS CLUSTERS
# ============================================

# Crear mapa base centrado en todas las salchipaperías
m = folium.Map(
    location=[sum([s["lat"] for s in salchipaperias]) / len(salchipaperias),
              sum([s["lon"] for s in salchipaperias]) / len(salchipaperias)],
    zoom_start=12,
    tiles="OpenStreetMap"
)

# Identificar todos los clusters existentes
clusters_unicos = sorted(set([s["cluster"] for s in salchipaperias]))

for cl in clusters_unicos:
    grupo = [s for s in salchipaperias if s["cluster"] == cl]
    num_nodos = len(grupo)

    # Crear FeatureGroup por cluster
    fg = folium.FeatureGroup(name=f"Cluster {cl}", show=True)

    # Marcadores
    for nodo in grupo:
        folium.Marker(
            location=[nodo["lat"], nodo["lon"]],
            popup=f"<b>ID:</b> {nodo['id']}<br><b>{nodo['nombre']}</b>",
            tooltip=f"{nodo['id']} – {nodo['nombre']}"
        ).add_to(fg)

    # Polígono del cluster usando bounding box convexa
    puntos = MultiPoint([(n["lon"], n["lat"]) for n in grupo])
    try:
        hull = puntos.convex_hull

        if hull.geom_type == "Polygon":
            coords = [[lat, lon] for lon, lat in hull.exterior.coords]

            folium.Polygon(
                locations=coords,
                color="blue",
                weight=2,
                fill=True,
                fill_opacity=0.15,
                popup=f"<b>Cluster {cl}</b><br>Nodos: {num_nodos}",
                tooltip=f"Cluster {cl} – {num_nodos} nodos"
            ).add_to(fg)

    except Exception as e:
        pass

    m.add_child(fg)

folium.LayerControl().add_to(m)

m

# ============================================
# ETAPA 5: Selección del cluster más pequeño y cálculo del centroide (lat/lon en grados)
# ============================================

# Contar nodos por cluster
cluster_counts = {}
for s in salchipaperias:
    cl = s.get("cluster")
    cluster_counts[cl] = cluster_counts.get(cl, 0) + 1

# Seleccionar cluster con menor número de nodos
cluster_seleccionado = min(cluster_counts, key=lambda k: cluster_counts[k])
nodos_cluster = [s for s in salchipaperias if s.get("cluster") == cluster_seleccionado]

print(f"Cluster seleccionado: {cluster_seleccionado} (nodos = {len(nodos_cluster)})\n")

# Calcular centroide en grados (media de latitudes y longitudes)
sum_lat = 0.0
sum_lon = 0.0
for nodo in nodos_cluster:
    sum_lat += float(nodo['lat'])
    sum_lon += float(nodo['lon'])

centroid_lat = sum_lat / len(nodos_cluster)
centroid_lon = sum_lon / len(nodos_cluster)

# Guardar el centroide en un diccionario (útil para etapas siguientes)
centroide = {"lat": round(centroid_lat, 7), "lon": round(centroid_lon, 7)}

# Imprimir resultados
print("Centroide del cluster (grados):")
print(f"  lat: {centroide['lat']}")
print(f"  lon: {centroide['lon']}\n")

print("Nodos del cluster seleccionado:")
for nodo in nodos_cluster:
    print(f"ID: {nodo['id']}")
    print(f"  Nombre   : {nodo['nombre']}")
    print(f"  Dirección: {nodo.get('direccion','')}")
    print(f"  Lat,Lon  : ({nodo['lat']}, {nodo['lon']})")
    print(f"  Demanda  : {nodo.get('demanda','N/A')} kg")
    print("-" * 50)

# ============================================
# ETAPA 6: MAPA CLUSTER SELECCIONADO + CENTROIDE
# ============================================

# Crear mapa centrado en el centroide del cluster seleccionado
m2 = folium.Map(
    location=[centroide["lat"], centroide["lon"]],
    zoom_start=13,
    tiles="OpenStreetMap"
)

# Feature group para este cluster
fg2 = folium.FeatureGroup(name=f"Cluster {cluster_seleccionado}", show=True)

# Añadir marcadores de nodos
for nodo in nodos_cluster:
    folium.Marker(
        location=[nodo["lat"], nodo["lon"]],
        popup=f"<b>ID:</b> {nodo['id']}<br><b>{nodo['nombre']}</b>",
        tooltip=f"{nodo['id']} – {nodo['nombre']}"
    ).add_to(fg2)

# Dibujar polígono del cluster
puntos = MultiPoint([(n["lon"], n["lat"]) for n in nodos_cluster])
try:
    hull = puntos.convex_hull

    if hull.geom_type == "Polygon":
        coords = [[lat, lon] for lon, lat in hull.exterior.coords]

        folium.Polygon(
            locations=coords,
            color="red",
            weight=2,
            fill=True,
            fill_opacity=0.18,
            popup=f"<b>Cluster seleccionado {cluster_seleccionado}</b><br>Nodos: {len(nodos_cluster)}",
            tooltip=f"Cluster {cluster_seleccionado} – {len(nodos_cluster)} nodos"
        ).add_to(fg2)

except:
    pass

# Marcar centroide
folium.CircleMarker(
    location=[centroide["lat"], centroide["lon"]],
    radius=8,
    color="black",
    fill=True,
    fill_color="yellow",
    fill_opacity=1,
    popup=f"<b>Centroide</b><br>Lat: {centroide['lat']}<br>Lon: {centroide['lon']}",
    tooltip="Centroide del cluster"
).add_to(fg2)

m2.add_child(fg2)
folium.LayerControl().add_to(m2)
m2

# ============================================
# ETAPA 7: Construcción de la matriz real de distancias (Google Distance Matrix API)
# ============================================

# Función para solicitar distancias desde 1 origen hacia varios destinos
def solicitar_distancias(api_key, origen, destinos):
    # Devuelve una lista con las distancias reales EN KILÓMETROS
    origin_str = f"{origen[0]},{origen[1]}"
    dest_str = "|".join([f"{lat},{lon}" for lat, lon in destinos])

    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin_str,
        "destinations": dest_str,
        "mode": "driving",
        "units": "metric",
        "key": api_key
    }

    r = requests.get(url, params=params)
    data = r.json()

    fila = []

    for elem in data["rows"][0]["elements"]:
        if elem["status"] != "OK":
            fila.append(float("inf"))   # en caso de error, distancia infinita
        else:
            metros = elem["distance"]["value"]
            km = metros / 1000.0
            fila.append(round(km, 3))   # redondeo limpio

    return fila


# Construcción de matriz de distancia (en km)
def construir_matriz(api_key, centroide, nodos_cluster):
    # Construye una matriz (N+1)x(N+1) en kilómetros. Donde la Fila/Columna 0 representa el centroide

    # Extraer nodos como lista de tuplas (lat, lon)
    nodos = [(float(n["lat"]), float(n["lon"])) for n in nodos_cluster]

    # Primer punto = centroide
    origenes = [(centroide["lat"], centroide["lon"])] + nodos

    destinos = origenes[:]  # copia exacta
    matriz = []

    for i, origen in enumerate(origenes):
        distancias = solicitar_distancias(api_key, origen, destinos)
        matriz.append(distancias)

    return matriz   # matriz oficial (lista de listas)

# Tabla usando Pandas
def generar_tabla_estetica(matriz, nodos_cluster):
    # Encabezados:
    # Columna 0 = Centroide
    nombres = ["Centroide"] + [n["id"] for n in nodos_cluster]

    # Crear DataFrame
    df = pd.DataFrame(matriz, columns=nombres, index=nombres)

    # Estilizar la tabla
    tabla_estilizada = (
        df.style
        .set_table_styles([
            # Estilo de la tabla completa
            {"selector": "table", "props": [("border-collapse", "collapse"),
                                            ("margin", "25px 0"),
                                            ("font-size", "14px"),
                                            ("font-family", "Arial"),
                                            ("text-align", "center")]},

            # Estilo de los encabezados
            {"selector": "th", "props": [("background-color", "#004080"),
                                         ("color", "white"),
                                         ("padding", "8px"),
                                         ("border", "1px solid #555")]},

            # Estilo de las celdas
            {"selector": "td", "props": [("border", "1px solid #888"),
                                         ("padding", "6px")]},
        ])
        .set_properties(**{"text-align": "center"})  # centro para todas las celdas
        .format("{:.3f}")  # fuerza formato a 3 decimales
    )

    return tabla_estilizada

# Llamado a la función
matriz_dist = construir_matriz(os.getenv('API_KEY'), centroide, nodos_cluster)
tabla_estetica = generar_tabla_estetica(matriz_dist, nodos_cluster)

# Obtener la direccion del centroide
def obtener_direccion(api_key, lat, lon):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "latlng": f"{lat},{lon}",
        "key": api_key
    }
    r = requests.get(url, params=params)
    data = r.json()

    if len(data.get("results", [])) == 0:
        return "Dirección no encontrada"

    return data["results"][0]["formatted_address"]

# Llamado a la función
direccion_centroide = obtener_direccion(os.getenv('API_KEY'), centroide["lat"], centroide["lon"])
tabla_estetica

# ==========================
# ETAPA 8: CVRP con SCIP
# ==========================

# Parámetros básicos
n = len(nodos_cluster)
C = range(1, n+1)            # clientes
N = list(range(n + 1))       # nodos
K = list(range(10))          # vehículos
distancia = matriz_dist         # matriz de distancias
demanda = [0.0] + [float(n['demanda']) for n in nodos_cluster] # demanda
Q = 5000.0                   # capacidad
TIME_LIMIT_SECONDS = 120     # límite de tiempo

index_to_label = ["D0"] + [str(n['id']) for n in nodos_cluster]

# Crear solver
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(TIME_LIMIT_SECONDS * 1000)

# Variables x[i][j][k]
x = {}
for i in N:
    for j in N:
        if i == j:
            continue
        for k in K:
            x[(i,j,k)] = solver.BoolVar(f"x_{i}_{j}_{k}")

# Variables f[i][j][k]
f = {}
for i in N:
    for j in N:
        if i == j:
            continue
        for k in K:
            f[(i,j,k)] = solver.NumVar(0.0, Q, f"f_{i}_{j}_{k}")

# y[k] = si el vehículo se usa
y = {k: solver.BoolVar(f"y_{k}") for k in K}

# z[i][k] = si el vehículo k atiende cliente i
z = {}
for i in C:
    for k in K:
        z[(i,k)] = solver.BoolVar(f"z_{i}_{k}")

# Objetivo: minimizar distancia
solver.Minimize(
    solver.Sum(distancia[i][j] * x[(i,j,k)]
               for i in N for j in N if i != j for k in K)
)

# ==========================
# Restricciones CVRP
# ==========================

# Cada cliente se atiende una vez
for j in C:
    solver.Add(solver.Sum(x[(i,j,k)] for i in N if i!=j for k in K) == 1)

# Relación entre x e z
for i in C:
    for k in K:
        solver.Add(solver.Sum(x[(i,j,k)] for j in N if j!=i) == z[(i,k)])
        solver.Add(solver.Sum(x[(h,i,k)] for h in N if h!=i) == z[(i,k)])

# z <= y
for i in C:
    for k in K:
        solver.Add(z[(i,k)] <= y[k])

# Salida y entrada del depósito
for k in K:
    solver.Add(solver.Sum(x[(0,j,k)] for j in N if j!=0) == y[k])
    solver.Add(solver.Sum(x[(i,0,k)] for i in N if i!=0) == y[k])

# Capacidad
for k in K:
    solver.Add(solver.Sum(demanda[i] * z[(i,k)] for i in C) <= Q * y[k])

# Flujo
for i in N:
    for j in N:
        if i == j: continue
        for k in K:
            solver.Add(f[(i,j,k)] <= Q * x[(i,j,k)])

# Flujo desde depósito = demanda servida
for k in K:
    solver.Add(
        solver.Sum(f[(0,j,k)] for j in N if j!=0)
        ==
        solver.Sum(demanda[i] * z[(i,k)] for i in C)
    )

# No entra flujo al depósito
for k in K:
    solver.Add(solver.Sum(f[(i,0,k)] for i in C) == 0)

# Conservación de flujo
for i in C:
    for k in K:
        solver.Add(
            solver.Sum(f[(h,i,k)] for h in N if h!=i) -
            solver.Sum(f[(i,j,k)] for j in N if j!=i)
            ==
            demanda[i] * z[(i,k)]
        )

# ==========================
# Resolver
# ==========================

start = time.time()
status = solver.Solve()
elapsed = time.time() - start

# ================================
#   SALIDA EN CONSOLA
# ================================
print("\n====================================================")
print("                 RESULTADO DEL MODELO")
print("====================================================")
print(f"Tiempo usado:           {round(elapsed, 2)} s")
print(f"Valor objetivo total:   {solver.Objective().Value():.3f} km")
print("====================================================\n")

if status != pywraplp.Solver.OPTIMAL and status != pywraplp.Solver.FEASIBLE:
    print("El solver no encontró solución factible dentro del tiempo límite.")
else:
    vehiculos_activos = [k for k in K if y[k].solution_value() > 0.5]

    print("Vehículos que operan:", vehiculos_activos)
    print(f"Total vehículos activos: {len(vehiculos_activos)}\n")

    for k in vehiculos_activos:
        print("----------------------------------------------------")
        print(f"               Vehículo {k}")
        print("----------------------------------------------------")

        # obtener sucesiones i->j
        succ = {}
        for i in N:
            for j in N:
                if i != j and x[(i,j,k)].solution_value() > 0.5:
                    succ[i] = j

        # reconstrucción de ruta con índices
        ruta_idx = [0]
        actual = 0
        while actual in succ:
            siguiente = succ[actual]
            ruta_idx.append(siguiente)
            actual = siguiente
            if actual == 0:
                break

        # reemplazar índices por labels reales (IDs)
        ruta_labels = [index_to_label[i] for i in ruta_idx]

        # distancia
        distancia_total = sum(distancia[i][j] for i, j in zip(ruta_idx[:-1], ruta_idx[1:]))

        # clientes asignados con IDs reales
        clientes_k_idx = [i for i in range(1, n+1) if z[(i,k)].solution_value() > 0.5]
        clientes_k_labels = [index_to_label[i] for i in clientes_k_idx]

        # impresión
        print(f"Ruta: {' -> '.join(ruta_labels)}")
        print(f"Clientes atendidos ({len(clientes_k_labels)}): {clientes_k_labels}")
        print(f"Distancia recorrida: {distancia_total:.3f} km")
        print(f"Carga servida: {sum(demanda[i] for i in clientes_k_idx):.1f} kg")
        print("----------------------------------------------------\n")

    # tabla final de asignaciones
    print("====================================================")
    print("      CLIENTES ASIGNADOS POR VEHÍCULO")
    print("====================================================")
    for k in vehiculos_activos:
        clientes_k = [i for i in range(1, n+1) if z[(i,k)].solution_value() > 0.5]
        clientes_label = [index_to_label[i] for i in clientes_k]
        print(f"Vehículo {k}: {clientes_label}")
    print("====================================================\n")

# ======================================
# ETAPA 9 - REPRESENTACIÓN CARTOGRÁFICA DE RUTAS POR VEHÍCULOS (FOLIUM)
# ======================================

# Vehículos activos (usar == 1 exactamente)
vehiculos_activos = [k for k in K if y[k].solution_value() == 1]

# Lookup coordenadas: id_cliente -> {'lat','lon'}
coords_lookup = {int(n['id']): {'lat': float(n['lat']), 'lon': float(n['lon'])}
                     for n in nodos_cluster}

# Lookup nombres: id_cliente -> nombre
nombres_por_id = {int(n['id']): n['nombre'] for n in nodos_cluster}

# Función para reconstruir ruta (índices 0..n)
def reconstruir_ruta_indices(k):
    succ = {}
    for i in N:
        for j in N:
            if i != j and x[(i, j, k)].solution_value() == 1:
                succ[i] = j
    ruta = [0]
    cur = 0
    pasos = 0
    while cur in succ:
        nxt = succ[cur]
        ruta.append(nxt)
        cur = nxt
        pasos += 1
        if cur == 0 or pasos > (len(N) + 5):
            break
    if ruta[-1] != 0:
        ruta.append(0)
    return ruta

# Reconstruir rutas y generar etiquetas usando index_to_label (ya tiene "D0" + ids)
rutas_indices = {}
rutas_labels = {}
for k in vehiculos_activos:
    ri = reconstruir_ruta_indices(k)
    rutas_indices[k] = ri
    # index_to_label[0] == "D0", index_to_label[i] == "<id>" for i>0
    rutas_labels[k] = [index_to_label[node] for node in ri]

# Crear mapa centrado en depósito (centroide)
m3 = folium.Map(location=[float(centroide["lat"]), float(centroide["lon"])], zoom_start=13, tiles="OpenStreetMap")

# marcador distintivo del depósito
folium.Marker(
    location=[float(centroide["lat"]), float(centroide["lon"])],
    popup="<b>DEPÓSITO (CENTROIDE)</b>",
    tooltip="DEPÓSITO",
    icon=folium.Icon(color="black", icon="home")
).add_to(m3)

# Paleta de colores
base_colors = ["red","blue","green","purple","orange","darkred","cadetblue","darkblue","darkgreen","pink"]
if len(vehiculos_activos) > len(base_colors):
    for _ in range(len(vehiculos_activos) - len(base_colors)):
        base_colors.append("#%06x" % random.randint(0, 0xFFFFFF))

# Dibujar rutas en orden, con marcadores numerados y popup/tooltip que muestran NOMBRE + ID
for idx, k in enumerate(vehiculos_activos):
    color = base_colors[idx % len(base_colors)]
    ruta_idx = rutas_indices[k]    # [0, i, j, ..., 0]
    ruta_lab = rutas_labels[k]     # ["D0", "37", "9", ...] using index_to_label

    # obtener coordenadas en orden (si falta coord, saltarla)
    coords_line = []
    for node in ruta_idx:
        if node == 0:
            coords_line.append([float(centroide["lat"]), float(centroide["lon"])])
        else:
            # index_to_label[node] es el id en string
            client_id = int(index_to_label[node])
            coord = coords_lookup.get(client_id)
            if coord is None:
                continue
            coords_line.append([coord['lat'], coord['lon']])

    # dibujar polilínea en el orden correcto
    if len(coords_line) >= 2:
        fg = folium.FeatureGroup(name=f"Vehículo {k}", show=True)
        folium.PolyLine(coords_line, color=color, weight=5, opacity=0.9, tooltip=f"Vehículo {k}").add_to(fg)

        # marcadores numerados y popups/tooltip con NOMBRE + ID
        for paso, (node, label) in enumerate(zip(ruta_idx, ruta_lab)):
            if node == 0:
                lat, lon = float(centroide["lat"]), float(centroide["lon"])
                nombre = "DEPÓSITO"
                label_text = "D0"
            else:
                # label es string con el id real (ej. '37') — seguro para int()
                client_id = int(label)
                coord = coords_lookup.get(client_id)
                if coord is None:
                    continue
                lat, lon = coord['lat'], coord['lon']
                nombre = nombres_por_id.get(client_id, "Sin nombre")
                label_text = label

            popup_html = f"<b>Vehículo {k}</b><br>Paso {paso}<br>{nombre}<br>ID: {label_text}"
            tooltip_text = f"{nombre} (ID {label_text}) — Paso {paso}"

            folium.CircleMarker(
                location=[lat, lon],
                radius=7,
                color=color,
                fill=True,
                fill_color=color,
                popup=popup_html,
                tooltip=tooltip_text
            ).add_to(fg)

            # etiqueta numérica visible con DivIcon
            folium.map.Marker(
                [lat, lon],
                icon=folium.DivIcon(html=f'<div style="font-size:12pt;color:{color};font-weight:bold;transform:translate(-8px,-10px)">{paso}</div>')
            ).add_to(fg)

        m3.add_child(fg)
    else:
        # caso raro: solo un punto
        if len(coords_line) == 1:
            folium.Marker(location=coords_line[0], popup=f"Vehículo {k} (sin ruta completa)", icon=folium.Icon(color=color)).add_to(m3)

# control de capas para activar/desactivar vehículos
folium.LayerControl().add_to(m3)

# Mostrar mapa en notebook
m3

# ======================================
# ETAPA 10 - ENVÍO DE CORREOS A LOS CONDUCTORES
# ======================================

# ======== CONFIGURA TU EMAIL ==========
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
APP_PASSWORD  = os.getenv('APP_PASSWORD')

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 465

# ======== LISTA DE CONDUCTORES (1 por vehículo) ========
# Debe haber al menos los vehículos posibles (0..9)

# SE DEBE DE PONER EL CORREO DESEADO PARA PROBAR EL ENVIO
conductores = [
    {"vehiculo": 0, "nombre": "Christian David Home Acero",      "email": "christian.home@uao.edu.co"},
    {"vehiculo": 1, "nombre": "Sebastian Leiton",     "email": "sebastian.leiton@uao.edu.co"},
    {"vehiculo": 2, "nombre": "Juan David Agudelo",     "email": "juan_dav.agudelo@uao.edu.co"},
    {"vehiculo": 3, "nombre": "Sharon Abella",       "email": "sharon.abella@uao.edu.co"},
    {"vehiculo": 4, "nombre": "Alan Basante",  "email": "alan.basante@uao.edu.co"},
    {"vehiculo": 5, "nombre": "Jorge Correa",  "email": "jorge.correa@uao.edu.co"},
    {"vehiculo": 6, "nombre": "Andrés Felipe Medina Díaz",   "email": "andres_fel.medina_d@uao.edu.co"},
    {"vehiculo": 7, "nombre": "Manuel Betancurt Pérez",  "email": "manuel.betancurt@uao.edu.co"},
    {"vehiculo": 8, "nombre": "Eddie Santiago Delgado Campo",    "email": "eddie.delgado@uao.edu.co"},
    {"vehiculo": 9, "nombre": "Laura Isabel Campo",   "email": "laura_isabel.campo@uao.edu.co"}
]

direcciones_por_id = {
    int(s["id"]): s["direccion"]
    for s in salchipaperias
}

# ========= PLANTILLA HTML DEL CORREO =========
HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{ font-family: Arial; background:#fafafa; }}
.card {{
    max-width: 680px; margin:20px auto; background:white;
    border-radius:12px; padding:20px;
    box-shadow:0 3px 12px rgba(0,0,0,0.15);
}}
h2 {{ color:#1f77b4; }}
table {{
    width:100%; border-collapse:collapse; margin-top:15px;
}}
th, td {{
    border-bottom:1px solid #ddd; padding:8px;
}}
th {{ background:#f3f5f7; }}
</style>
</head>
<body>
<div class="card">
<h2>Asignación de Ruta – Vehículo {vehiculo}</h2>

<p>Hola <b>{nombre}</b>,<br>
Tu vehículo ha sido seleccionado para realizar un recorrido.<br>
A continuación encuentras la lista de clientes en el orden exacto que debes visitar:</p>

<table>
<thead>
<tr><th>Orden</th><th>ID</th><th>Nombre</th><th>Direccion</th><th>Demanda (kg)</th></tr>
</thead>
<tbody>
{rows}
</tbody>
</table>

<p><b>Carga total a transportar 📦:</b> {carga_total:.1f} kg</p>
<p>Te deseamos un excelente viaje y un recorrido seguro. ♥️</p>
</div>
</body>
</html>
"""


# ========= FUNCIÓN PARA ENVIAR EMAIL =========
def enviar_email_html(para, asunto, html):
    msg = MIMEMultipart("alternative")
    msg.set_charset("utf-8")
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = para
    msg["Subject"] = asunto
    msg.attach(MIMEText(html, "html", "utf-8"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=ctx) as server:
        server.login(EMAIL_ADDRESS, APP_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, para, msg.as_string())


# ========= PROCESAR VEHÍCULOS ACTIVOS =========
enviados = []

for k in vehiculos_activos:
    # buscar conductor para el vehículo k
    driver = next((c for c in conductores if c["vehiculo"] == k), None)
    if driver is None:
        print(f"⚠️ No hay conductor para vehículo {k}. Se omite.")
        continue

    # obtener ruta en labels
    ruta_labels = rutas_labels[k]     # ej: ["D0","37","9","D0"]
    ruta_indices = rutas_indices[k]   # ej: [0,7,5,0]

    # Construir filas HTML
    rows = ""
    carga_total = 0.0
    for paso, (idx, label) in enumerate(zip(ruta_indices, ruta_labels)):
        if label == "D0":
            nombre_local = "DEPÓSITO"
            direccion = direccion_centroide
            demanda_local = 0.0
            id_text = "D0"
        else:
            client_id = int(label)
            nombre_local = nombres_por_id.get(client_id, "Sin nombre")
            direccion = direcciones_por_id.get(client_id, "Sin dirección")
            demanda_local = demanda[idx]
            id_text = label

        carga_total += demanda_local
        rows += f"<tr><td>{paso}</td><td>{id_text}</td><td>{nombre_local}</td><td>{direccion}</td><td>{demanda_local:.1f}</td></tr>\n"

    # armar el html final
    html = HTML_TEMPLATE.format(
        vehiculo=k,
        nombre=driver["nombre"],
        rows=rows,
        carga_total=carga_total
    )

    # enviar
    try:
        enviar_email_html(driver["email"], f"Ruta asignada – Vehículo {k}", html)
        enviados.append((k, driver["email"]))
        time.sleep(0.5)
    except Exception as e:
        print(f"❌ Error enviando correo al vehículo {k}: {e}")


# ======= Resumen final =======
print("\n============================")
print(" ENVÍO DE CORREOS FINALIZADO")
print("============================")
for v, mail in enviados:
    print(f" Vehículo {v} → {mail}")