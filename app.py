import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import os
from datetime import datetime
import time

# ---------------------------------------------------------
# CONFIGURATION DE L'APPLICATION + THÈME SOMBRE
# ---------------------------------------------------------
st.set_page_config(
    page_title="Station Météo — Saint‑Cyprien‑de‑Napierville",
    page_icon="⛅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ✅ CSS pour thème sombre personnalisé
st.markdown("""
    <style>
        body {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }
        .stApp {
            background-color: #1e1e1e;
        }
        h1, h2, h3, h4, h5, h6, p, div, span {
            color: #e0e0e0 !important;
        }
        .stMetric {
            background-color: #2a2a2a !important;
            border-radius: 8px;
            padding: 10px;
        }
        .stButton>button {
            background-color: #444 !important;
            color: white !important;
            border-radius: 6px;
            border: 1px solid #777 !important;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# INITIALISATION DES VARIABLES
# ---------------------------------------------------------
if "last_refresh_time" not in st.session_state:
    st.session_state["last_refresh_time"] = None

if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = time.time()

auto_update = False
if time.time() - st.session_state["last_refresh"] > 300:
    st.session_state["last_refresh"] = time.time()
    auto_update = True

# ---------------------------------------------------------
# TITRE
# ---------------------------------------------------------
st.title("🌤️ Station Météo — Saint‑Cyprien‑de‑Napierville")

# ✅ Enregistrer l'heure de la visite si aucune donnée n'existe encore
if st.session_state["last_refresh_time"] is None:
    st.session_state["last_refresh_time"] = datetime.now()

# ---------------------------------------------------------
# LIGNE POINTILLÉE SOUS LE TITRE
# ---------------------------------------------------------
st.markdown("""
    <div style="
        border-top: 2px dashed #888;
        margin-top: 5px;
        margin-bottom: 15px;
    "></div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# BOUTON + INFOS
# ---------------------------------------------------------
if st.button("🔄 Rafraîchir maintenant"):
    st.session_state["manual_update"] = True

t = st.session_state["last_refresh_time"]
st.markdown(f"**Dernier rafraîchissement :** {t.strftime('%Y-%m-%d %H:%M:%S')}")

elapsed = time.time() - st.session_state["last_refresh"]
remaining = max(0, 300 - int(elapsed))
minutes, seconds = divmod(remaining, 60)
st.markdown(f"⏳ **Prochaine mise à jour automatique dans :** {minutes:02d}:{seconds:02d}")

# ---------------------------------------------------------
# FONCTIONS
# ---------------------------------------------------------
def convertir_colonnes(df):
    colonnes = ["Pression (hPa)", "Température (°C)", "Humidité (%)", "Vent (km/h)"]
    for col in colonnes:
        df[col] = df[col].astype(str).str.replace(",", ".").astype(float)
    return df

def analyse_prevision(df, now, heures):
    df_recent = df[df["Datetime"] >= (now - pd.Timedelta(hours=heures))]
    if len(df_recent) < 2:
        return f"{heures}h: pas assez de données"
    p_now = df_recent["Pression (hPa)"].iloc[-1]
    p_old = df_recent["Pression (hPa)"].iloc[0]
    dp = p_now - p_old
    if dp >= 1:
        tendance = "amélioration"
    elif dp <= -1:
        tendance = "détérioration"
    else:
        tendance = "stable"
    return f"{heures}h: {tendance}"

def charger_csv():
    now = datetime.now()
    year_month = now.strftime("%Y-%m")
    csv_path = f"data/meteo_{year_month}.csv"
    if not os.path.exists("data"):
        os.makedirs("data")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df = convertir_colonnes(df)
        df["Datetime"] = pd.to_datetime(df["Datetime"])
        return df, csv_path
    else:
        df = pd.DataFrame(columns=[
            "Date", "Heure", "Pression (hPa)", "Température (°C)",
            "Humidité (%)", "Vent (km/h)", "Prévision", "Datetime"
        ])
        return df, csv_path

def recuperer_meteo():
    url = "https://api.open-meteo.com/v1/forecast?latitude=45.25&longitude=-73.50&current=temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m"
    response = requests.get(url).json()
    return response["current"]

# ---------------------------------------------------------
# CHARGEMENT DES DONNÉES
# ---------------------------------------------------------
df, csv_path = charger_csv()
st.session_state["df"] = df

if len(df) > 0:
    now = datetime.now()
    df = df[df["Datetime"] >= (now - pd.Timedelta(days=5))]
    df = convertir_colonnes(df)
    df.to_csv(csv_path, index=False)
    st.session_state["df"] = df

# ---------------------------------------------------------
# MISE À JOUR AUTOMATIQUE / MANUELLE
# ---------------------------------------------------------
def ajouter_mesure():
    global df
    current = recuperer_meteo()
    now = datetime.now()
    st.session_state["last_refresh_time"] = now
    df_new = pd.DataFrame([{
        "Date": now.strftime("%Y-%m-%d"),
        "Heure": now.strftime("%H:%M:%S"),
        "Pression (hPa)": float(current["pressure_msl"]),
        "Température (°C)": float(current["temperature_2m"]),
        "Humidité (%)": float(current["relative_humidity_2m"]),
        "Vent (km/h)": float(current["wind_speed_10m"]),
        "Prévision": "",
        "Datetime": now
    }])
    df = pd.concat([df, df_new], ignore_index=True)
    df.at[df.index[-1], "Prévision"] = (
        f"{analyse_prevision(df, now, 3)} | "
        f"{analyse_prevision(df, now, 6)} | "
        f"{analyse_prevision(df, now, 12)}"
    )
    df.to_csv(csv_path, index=False)
    st.session_state["df"] = df
    st.rerun()

if auto_update:
    ajouter_mesure()

if "manual_update" in st.session_state and st.session_state["manual_update"]:
    st.session_state["manual_update"] = False
    ajouter_mesure()

# ---------------------------------------------------------
# LIGNE POINTILLÉE AVANT "Données météorologiques actuelles"
# ---------------------------------------------------------
st.markdown("""
    <div style="
        border-top: 2px dashed #888;
        margin-top: 20px;
        margin-bottom: 15px;
    "></div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DONNÉES ACTUELLES
# ---------------------------------------------------------
st.subheader("📡 Données météorologiques actuelles")

if len(df) > 0:
    last = df.iloc[-1]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pression", f"{last['Pression (hPa)']} hPa")
    col2.metric("Température", f"{last['Température (°C)']} °C")
    col3.metric("Humidité", f"{last['Humidité (%)']} %")
    col4.metric("Vent", f"{last['Vent (km/h)']} km/h")
else:
    st.info("Aucune donnée disponible. Cliquez sur 🔄 Rafraîchir maintenant.")

# ---------------------------------------------------------
# LIGNE POINTILLÉE AVANT "Prévisions"
# ---------------------------------------------------------
st.markdown("""
    <div style="
        border-top: 2px dashed #888;
        margin-top: 20px;
        margin-bottom: 15px;
    "></div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# PRÉVISIONS
# ---------------------------------------------------------
st.subheader("🔮 Prévisions")

if len(df) > 0:
    now = datetime.now()
    st.write(analyse_prevision(df, now, 3))
    st.write(analyse_prevision(df, now, 6))
    st.write(analyse_prevision(df, now, 12))

# ---------------------------------------------------------
# LIGNE POINTILLÉE AVANT LE GRAPHIQUE
# ---------------------------------------------------------
st.markdown("""
    <div style="
        border-top: 2px dashed #888;
        margin-top: 20px;
        margin-bottom: 15px;
    "></div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# GRAPHIQUE
# ---------------------------------------------------------
st.subheader("📈 Graphique multi‑courbes (5 derniers jours)")

if len(df) > 0:
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.plot(df["Datetime"], df["Pression (hPa)"], color="cyan")
    ax1.set_ylabel("Pression (hPa)", color="cyan")
    ax2 = ax1.twinx()
    ax2.plot(df["Datetime"], df["Température (°C)"], color="red")
    ax2.set_ylabel("Température (°C)", color="red")
    ax3 = ax1.twinx()
    ax3.spines["right"].set_position(("outward", 60))
    ax3.plot(df["Datetime"], df["Vent (km/h)"], color="lime")
    ax3.set_ylabel("Vent (km/h)", color="lime")
    ax4 = ax1.twinx()
    ax4.spines["right"].set_position(("outward", 120))
    ax4.plot(df["Datetime"], df["Humidité (%)"], color="violet")
    ax4.set_ylabel("Humidité (%)", color="violet")
    st.pyplot(fig)

# ---------------------------------------------------------
# LIGNE POINTILLÉE AVANT L'HISTORIQUE
# ---------------------------------------------------------
st.markdown("""
    <div style="
        border-top: 2px dashed #888;
        margin-top: 20px;
        margin-bottom: 15px;
    "></div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HISTORIQUE
# ---------------------------------------------------------
st.subheader("📅 Historique des 5 derniers jours")

st.dataframe(df, use_container_width=True)