# 🚚 CVRP para la Distribución de Salchipapas en Cali

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python">
  <img src="https://img.shields.io/badge/OR--Tools-SCIP-orange?style=for-the-badge">
  <img src="https://img.shields.io/badge/K--Means-Clustering-green?style=for-the-badge">
  <img src="https://img.shields.io/badge/Folium-Maps-success?style=for-the-badge">
</p>

<p align="center">
  Proyecto académico desarrollado para la asignatura de <b>Investigación de Operaciones</b>,
  donde se resuelve un <b>Capacitated Vehicle Routing Problem (CVRP)</b> utilizando datos reales
  de salchipaperías ubicadas en la ciudad de Cali, Colombia.
</p>

---

## 📌 Descripción

Este proyecto implementa una solución completa para un problema de distribución logística utilizando técnicas de:

- 📍 Georreferenciación
- 🤖 Clustering con K-Means
- 🗺️ Google Distance Matrix API
- 📦 Capacitated Vehicle Routing Problem (CVRP)
- ⚙️ Programación Entera Mixta (MILP)
- 🚚 Optimización de rutas con OR-Tools
- 📧 Envío automático de asignaciones por correo electrónico

A partir de más de 80 salchipaperías distribuidas en Cali, el sistema identifica zonas geográficas, construye una matriz de distancias reales y genera rutas óptimas minimizando la distancia total recorrida.

---

## ✨ Características

### 📊 Procesamiento de Datos

- Lectura automática del dataset CSV.
- Asignación aleatoria de demandas.
- Preparación y transformación geográfica de coordenadas.

### 🤖 Clustering Inteligente

- Aplicación de K-Means.
- División automática en 3 regiones.
- Selección del clúster más adecuado para optimización.

### 🗺️ Distancias Reales

- Integración con Google Distance Matrix API.
- Distancias calculadas sobre la red vial real.

### 🚚 Optimización CVRP

- Hasta 10 vehículos disponibles.
- Restricciones de capacidad.
- Minimización de kilómetros recorridos.
- Resolución mediante SCIP Solver.

### 📍 Visualización

- Mapas interactivos con Folium.
- Visualización de clusters.
- Visualización de rutas optimizadas.

### 📧 Automatización

- Generación de correos HTML.
- Envío automático de rutas a conductores.

---

## 📂 Estructura del Proyecto

```text
.
├── cvrp.py
├── salchipaperias.csv
├── requirements.txt
├── .env.template
└── README.md
```

| Archivo              | Descripción                          |
| -------------------- | ------------------------------------ |
| `cvrp.py`            | Implementación completa del proyecto |
| `salchipaperias.csv` | Dataset de salchipaperías en Cali    |
| `requirements.txt`   | Dependencias del proyecto            |
| `.env.template`      | Variables de entorno necesarias      |

---

## 🛠️ Tecnologías Utilizadas

| Tecnología                 | Uso                   |
| -------------------------- | --------------------- |
| Python                     | Desarrollo principal  |
| Pandas                     | Manipulación de datos |
| NumPy                      | Operaciones numéricas |
| Scikit-Learn               | K-Means               |
| OR-Tools                   | Optimización          |
| SCIP                       | Solver MIP            |
| Folium                     | Mapas interactivos    |
| Google Distance Matrix API | Distancias reales     |
| SMTP                       | Envío de correos      |

---

## ⚙️ Instalación

### 1. Clonar repositorio

```bash
git clone https://github.com/eddiedev14/cvrp-salchipaperias-io.git

cd cvrp-salchipaperias-io
```

### 2. Crear entorno virtual

```bash
python -m venv venv
```

### 3. Activarlo

#### Windows

```bash
venv\Scripts\activate
```

#### Linux/Mac

```bash
source venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## 🔑 Configuración

Copiar el archivo:

```bash
.env.template
```

como:

```bash
.env
```

y completar:

```env
API_KEY=TU_GOOGLE_MAPS_API_KEY

EMAIL_ADDRESS=TU_CORREO

EMAIL_APP_PASSWORD=TU_APP_PASSWORD
```

---

## ▶️ Ejecución

```bash
python cvrp.py
```

---

## 👨‍💻 Autores

- Eddie Santiago Delgado Campo
- Andrés Felipe Medina Díaz
- Christian David Home Acero
