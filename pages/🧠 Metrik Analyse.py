# 📁 pages/VideoResult.py
import base64
import os
import streamlit as st
import time
import requests
from PIL import Image
from io import BytesIO
from config import API_BASE, SESSION_ROOT

st.set_page_config(
    page_title="Video Ergebnis | FootballAI",
    page_icon="⚽",
    layout="wide"
)

session_id = st.session_state.get("session_id")
if not session_id:
    st.warning("⚠️ Keine Session-ID gefunden.")
    st.stop()
if "active_session" in st.session_state:
    del st.session_state["active_session"]

st.title("🧠 Metrik Analyse")
st.write("")
st.markdown(f"**📁 Session-ID:** `{session_id}`")
st.info("🔐 Bitte notiere dir diese Session-ID, um später wieder auf das Ergebnis zugreifen zu können.")
st.session_state["run_annotate"] = False


if not st.session_state["redirect_to_only_video_download"]:
    progress_bar = st.progress(0, text="Initialisiere...")

    def check_progress():
        try:
            r = requests.get(f"{API_BASE}/progress/{session_id}", timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"[WARN] Fortschritt nicht abrufbar: {e}")
        return {"current": 0, "total": 1}

    # 🔁 Polling-Schleife
    progress_data = {"current": 0, "total": 1}
    last_update = time.time()
    while True:
        now = time.time()
        if now - last_update >= 2:
            progress_data = check_progress()
            last_update = now

        current = progress_data["current"]
        total = progress_data["total"]
        pct = current / total if total > 0 else 0

        progress_bar.progress(pct, text=f"🎥 Fortschritt: {int(pct * 100)}%")

        if current >= total:
            st.success("✅ Annotiertes Video fertiggestellt! Das Video ist jeden Moment zum Download verfügbar.")
            break

        time.sleep(2)

st.markdown("---")
st.subheader("🔢 KPI Übersicht zur analysierten Sequenz")
st.write("")

# 📊 Metriken anzeigen

r = requests.get(f"{API_BASE}/metrics-summary/{session_id}")
team1 = None
team2 = None

if r.status_code == 200:
    response = r.json()
    summary = response["metrics"]
    team1 = response["team_1"]
    team2 = response["team_2"]

    # 🧠 Metriken umbenennen und gruppieren
    metrics_mapping = {
        "team_1_possession_percent": ("Ballbesitz (%)", "team1"),
        "team_2_possession_percent": ("Ballbesitz (%)", "team2"),
        "team_1_goals": ("Tore", "team1"),
        "team_2_goals": ("Tore", "team2"),
        "team_1_shots": ("Torschüsse", "team1"),
        "team_2_shots": ("Torschüsse", "team2"),
        "team_1_distance_m": ("Distanz (m)", "team1"),
        "team_2_distance_m": ("Distanz (m)", "team2"),
        "team_1_avg_speed_kmh": ("Ø Geschwindigkeit (km/h)", "team1"),
        "team_2_avg_speed_kmh": ("Ø Geschwindigkeit (km/h)", "team2"),
        "space_control_avg_team_1": ("Raumkontrolle gesamt (%)", "team1"),
        "space_control_avg_team_2": ("Raumkontrolle gesamt (%)", "team2"),
        "thirds_control_avg_defensive_team_1": ("Defensivdrittel Kontrolle (%)", "team1"),
        "thirds_control_avg_defensive_team_2": ("Defensivdrittel Kontrolle (%)", "team2"),
        "thirds_control_avg_middle_team_1": ("Mitteldrittel Kontrolle (%)", "team1"),
        "thirds_control_avg_middle_team_2": ("Mitteldrittel Kontrolle (%)", "team2"),
        "thirds_control_avg_attacking_team_1": ("Angriffsdrittel Kontrolle (%)", "team1"),
        "thirds_control_avg_attacking_team_2": ("Angriffsdrittel Kontrolle (%)", "team2"),
    }

    # 🔢 Aufteilen nach Team
    team1_metrics = {v[0]: summary[k] for k, v in metrics_mapping.items() if v[1] == "team1"}
    team2_metrics = {v[0]: summary[k] for k, v in metrics_mapping.items() if v[1] == "team2"}

    def colored_header(team: dict):
        """
        Zeigt einen farbigen Header mit Farbkästchen und Teamnamen an.

        Args:
            team (dict): z. B. {"name": "VFB", "color": "#0000FF"}
        """
        st.markdown(f"""
        <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 10px;'>
            <div style='width: 18px; height: 18px; background-color: {team['color']}; border-radius: 3px;'></div>
            <div style='color: white; font-weight: bold; font-size: 25px;'>{team['name']}</div>
        </div>
        """, unsafe_allow_html=True)

    def colored_metric(label, value, color):
        st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <div style="font-size: 1rem; color: white;">{label}</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #14B8A6;">{value}</div>
            </div>
        """, unsafe_allow_html=True)

    # 📐 Anzeige in zwei Spalten
    col_l, col_r = st.columns(2)
    with col_l:
        colored_header(team1)
        for label, value in team1_metrics.items():
            label_clean = label.replace("team_1_", "").replace("_", " ")
            colored_metric(label_clean, value, team1["color"])

    with col_r:
        colored_header(team2)
        for label, value in team2_metrics.items():
            label_clean = label.replace("team_2_", "").replace("_", " ")
            colored_metric(label_clean, value, team2["color"])

else:
    st.warning("⚠️ Konnte Metriken nicht laden.")


st.markdown("---")
st.markdown("## 📊 KPI-Daten exportieren")
st.write("")

col1, middle, col2 = st.columns(3)

with col1:
    st.markdown(
        f"""
        <a href="{API_BASE}/metrics-excel/{session_id}" style="text-decoration: none;">
            <div style="
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                padding: 10px 16px;
                border: 1px solid #ccc;
                border-radius: 8px;
                background-color: transparent;
                color: white;
                font-weight: 500;
                font-size: 16px;
                transition: background-color 0.2s ease;
            " onmouseover="this.style.backgroundColor='#33333322'" onmouseout="this.style.backgroundColor='transparent'">
                📈 <span>Excel herunterladen</span>
            </div>
        </a>
        """,
        unsafe_allow_html=True
    )
with middle:
    download_path = f"./temp/heatmaps_{session_id}.zip"
    
    # Falls Datei noch nicht existiert, dann erst anfordern und speichern
    if not os.path.exists(download_path):
        r = requests.get(f"{API_BASE}/generate-heatmaps/{session_id}")
        if r.status_code == 200:
            os.makedirs("./temp", exist_ok=True)
            with open(download_path, "wb") as f:
                f.write(r.content)
        else:
            st.error("❌ Fehler beim Erzeugen der Heatmaps.")
    
    # Prüfen, ob Datei nun lokal existiert und Download-Link anbieten
    if os.path.exists(download_path):
        with open(download_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            st.markdown(
                f"""
                <a href="data:application/zip;base64,{b64}" download="heatmaps.zip" style="text-decoration: none;">
                    <div style="
                    display: flex; 
                    align-items: center;
                    justify-content: center;
                    gap: 10px; 
                    padding: 10px 16px; 
                    border: 1px solid #ccc; 
                    border-radius: 8px;
                    background-color: 
                    transparent; color: white; 
                    font-weight: 500; 
                    font-size: 16px;
                    transition: background-color 0.2s ease;"
                    onmouseover="this.style.backgroundColor='#33333322'" onmouseout="this.style.backgroundColor='transparent'">
                        🗺️ <span>Laufwege herunterladen</span>
                    </div>
                </a>
                """,
                unsafe_allow_html=True
            )
with col2:
    video_url = f"{API_BASE}/annotated-video/{session_id}"
    video_check = requests.get(video_url)
    
    if video_check.status_code == 200:
        st.markdown(
            f"""
            <a href="{video_url}" download style="text-decoration: none;">
                <div style="
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 10px;
                    padding: 10px 16px;
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    background-color: transparent;
                    color: white;
                    font-weight: 500;
                    font-size: 16px;
                    transition: background-color 0.2s ease;
                " onmouseover="this.style.backgroundColor='#33333322'" onmouseout="this.style.backgroundColor='transparent'">
                    📥 <span>Spielsequenz mit Metriken herunterladen</span>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )
    else:
        st.error("⚠️ Annotiertes Video noch nicht verfügbar – bitte Seite später erneut laden.")

st.markdown("---")

st.markdown(f'## 📷 Laufwege der Teams')
# Zwei Spalten erzeugen
col1, col2 = st.columns(2)

# URL zu den Heatmaps
url_team1 = f'{API_BASE}/heatmap/{session_id}/{team1["name"]}'
url_team2 = f'{API_BASE}/heatmap/{session_id}/{team2["name"]}'

# Bild für Team 1
with col1:
    r1 = requests.get(url_team1)
    if r1.status_code == 200:
        image1 = Image.open(BytesIO(r1.content))
        st.image(image1, caption=f'Laufwege des {team1["name"]} - Abbildung ist im obrigen Download enthalten.', use_container_width=True)
    else:
        st.error("❌ Heatmap für Team 1 nicht gefunden.")

# Bild für Team 2
with col2:
    r2 = requests.get(url_team2)
    if r2.status_code == 200:
        image2 = Image.open(BytesIO(r2.content))
        st.image(image2, caption=f'Laufwege des {team2["name"]} - Abbildung ist im obrigen Download enthalten.', use_container_width=True)
    else:
        st.error("❌ Heatmap für Team 2 nicht gefunden.")

