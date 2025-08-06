import base64
import os
from config import API_BASE_PATH
import pandas as pd
import streamlit as st
import time
import requests
from PIL import Image
from io import BytesIO
from config import SESSION_ROOT
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Video Results | FootballAI",
    page_icon="⚽",
    layout="wide"
)
API_BASE = st.secrets["API_BASE"] if "API_BASE" in st.secrets else os.getenv("API_BASE", "http://localhost:8000")

def api_url(endpoint: str) -> str:
    return f"{API_BASE.rstrip('/')}{API_BASE_PATH.rstrip('/')}/{endpoint.lstrip('/')}"

session_id = st.session_state.get("session_id")
if not session_id:
    st.warning("⚠️ No session ID found.")
    st.stop()
if "active_session" in st.session_state:
    del st.session_state["active_session"]

if "automatic_assignment" in st.session_state:
    del st.session_state["automatic_assignment"]

st.title("🧠 Metric Analysis")
st.write("")
st.markdown(f"**📁 Session ID:** `{session_id}`")
st.info("🔐 Please save this session ID to revisit the results later.")
st.session_state["run_annotate"] = False

if not st.session_state["redirect_to_only_video_download"]:
    progress_bar = st.progress(0, text="Initializing...")

    def check_progress():
        try:
            r = requests.get(api_url(f"{session_id}/progress/annotator"), timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"[WARN] Could not retrieve progress: {e}")
        return None

    progress_data = None
    for _ in range(10):
        progress_data = check_progress()
        if progress_data:
            break
        time.sleep(2)

    if not progress_data:
        st.warning("⏳ Could not retrieve progress data...")
        st.stop()

    last_update = time.time()
    while True:
        now = time.time()
        if now - last_update >= 2:
            new_progress = check_progress()
            if new_progress:
                progress_data = new_progress
            last_update = now

        current = progress_data["current"]
        total = progress_data["total"]
        pct = current / total if total > 0 else 0

        progress_bar.progress(pct, text=f"🎥 Progress: {int(pct * 100)}%")

        if current >= total:
            st.success("✅ Annotated video completed! The video will be available for download shortly.")
            break

        time.sleep(2)

def wait_for_annotation_ready(session_id, max_wait=30):
    for _ in range(max_wait):
        try:
            r = requests.get(api_url(f"{session_id}"))
            if r.status_code == 200:
                info = r.json()
                if info.get("annotated_exists", False):
                    return True
        except:
            pass
        time.sleep(3)
    return False

# 📊 Display metrics
if wait_for_annotation_ready(session_id):
    st.markdown("---")
    st.subheader("🔢 KPI Summary of the Analyzed Sequence")
    st.write("")

    r = requests.get(api_url(f"{session_id}/results/metrics/summary"))
    team1 = None
    team2 = None

    if r.status_code == 200:
        response = r.json()
        summary = response["metrics"]
        team1 = response["team_1"]
        team2 = response["team_2"]

        metrics_mapping = {
            "team_1_possession_percent": ("Possession (%)", "team1"),
            "team_2_possession_percent": ("Possession (%)", "team2"),
            "team_1_goals": ("Goals", "team1"),
            "team_2_goals": ("Goals", "team2"),
            "team_1_shots": ("Shots", "team1"),
            "team_2_shots": ("Shots", "team2"),
            "team_1_passes": ("Passes", "team1"),
            "team_2_passes": ("Passes", "team2"),
            "team_1_distance_m": ("Distance (m)", "team1"),
            "team_2_distance_m": ("Distance (m)", "team2"),
            "team_1_avg_speed_kmh": ("Avg. Speed (km/h)", "team1"),
            "team_2_avg_speed_kmh": ("Avg. Speed (km/h)", "team2"),
            "space_control_avg_team_1": ("Overall Space Control (%)", "team1"),
            "space_control_avg_team_2": ("Overall Space Control (%)", "team2"),
            "thirds_control_avg_defensive_team_1": ("Defensive Control (%)", "team1"),
            "thirds_control_avg_defensive_team_2": ("Defensive Control (%)", "team2"),
            "thirds_control_avg_middle_team_1": ("Midfield Control (%)", "team1"),
            "thirds_control_avg_middle_team_2": ("Midfield Control (%)", "team2"),
            "thirds_control_avg_attacking_team_1": ("Offensive Control (%)", "team1"),
            "thirds_control_avg_attacking_team_2": ("Offensive Control (%)", "team2"),
        }

        team1_metrics = {v[0]: summary[k] for k, v in metrics_mapping.items() if v[1] == "team1"}
        team2_metrics = {v[0]: summary[k] for k, v in metrics_mapping.items() if v[1] == "team2"}

        def colored_header(team: dict):
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

        col_l, col_r = st.columns(2)
        with col_l:
            colored_header(team1)
            for label, value in team1_metrics.items():
                colored_metric(label, value, team1["color"])

        with col_r:
            colored_header(team2)
            for label, value in team2_metrics.items():
                colored_metric(label, value, team2["color"])

        st.markdown("---")
        st.subheader("📊 Radar Comparison of the Teams")
        st.markdown("""
        <div style='font-size: 1rem; line-height: 1.6;'>
            The radar chart provides a compact overview of key metrics in direct comparison. 
            Each value is normalized (0–100 %) to allow equal scaling. The closer the area gets to the edge, the more dominant the performance in that aspect.
        </div>
        """, unsafe_allow_html=True)
        with st.expander("📊 Show Radar Chart Interpretation"):
            st.markdown("""
            <ul>
                <li><b>Shots</b> and <b>Goals</b> indicate offensive effectiveness.</li>
                <li><b>Possession</b> reflects match control – a high value signals dominant play and passing sequences.</li>
                <li><b>Distance</b> and <b>Speed</b> reflect physical effort and tempo – important for transitions and pressing intensity.</li>
                <li><b>Control Zones</b> indicate spatial dominance across field thirds.</li>
            </ul>
            """, unsafe_allow_html=True)

        # Metriken fürs Spiderweb
        spider_labels = [
            "Possession (%)",
            "Goals",
            "Shots",
            "Distance (m)",
            "Avg. Speed (km/h)",
            "Offensive Control (%)",
            "Midfield Control (%)",
            "Defensive Control (%)"
        ]


        # Werte für beide Teams vorbereiten
        values_team1 = []
        values_team2 = []
        hover_team1 = []
        hover_team2 = []
        categories = spider_labels.copy()

        for label in spider_labels:
            val1 = team1_metrics.get(label, 0)
            val2 = team2_metrics.get(label, 0)

            if "%" in label:
                # ✅ Prozentwerte direkt verwenden
                norm1 = val1
                norm2 = val2
            else:
                # 📏 Absolute Werte normieren auf 0–100
                max_val = max(val1, val2, 1e-5)
                norm1 = val1 / max_val * 100
                norm2 = val2 / max_val * 100

            values_team1.append(round(norm1, 2))
            values_team2.append(round(norm2, 2))
            hover_team1.append(f"{val1:.2f}")
            hover_team2.append(f"{val2:.2f}")

        # Polygon schließen
        values_team1.append(values_team1[0])
        values_team2.append(values_team2[0])
        hover_team1.append(hover_team1[0])
        hover_team2.append(hover_team2[0])
        categories.append(categories[0])

        # 🕸️ Spiderweb zeichnen
        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=values_team1,
            theta=categories,
            fill='toself',
            name=team1["name"],
            marker_color=team1["color"],
            hovertext=hover_team1,
            hovertemplate="%{theta}<br>" + team1["name"] + ": %{hovertext}",
            opacity=0.7
        ))

        fig.add_trace(go.Scatterpolar(
            r=values_team2,
            theta=categories,
            fill='toself',
            name=team2["name"],
            marker_color=team2["color"],
            hovertext=hover_team2,
            hovertemplate="%{theta}<br>" + team2["name"] + ": %{hovertext}",
            opacity=0.7
        ))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            template="plotly_dark",
            height=500,
            margin=dict(t=40, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)


    else:
        st.warning("⚠️ Konnte Metriken nicht laden.")

    st.markdown("---")
    # Getting Team Directions from Backend
    dir_map = {
        "left_to_right": "left to right",
        "right_to_left": "right to left"
    }
    dir1 = "unbekannt"
    dir2 = "unbekannt"

    try:
        team_direction_result = requests.get(api_url(f"{session_id}/team-assignment/directions"))


        if team_direction_result.status_code == 200:
            data = team_direction_result.json()
            dir1 = data.get("team_1_direction", "unbekannt")
            dir2 = data.get("team_2_direction", "unbekannt")
        else:
            st.error(f"Fehler beim Laden der Teamrichtungen: {team_direction_result.status_code}")

    except Exception as e:
        st.error(f"Verbindungsfehler: {str(e)}")


    dir1_text = dir_map.get(dir1, "unbekannt")
    dir2_text = dir_map.get(dir2, "unbekannt")

    st.markdown("## 📷 Team Movement Heatmaps")

    st.markdown("""
    <style>
    .small-expander-text {
        font-size: 0.82rem !important;
        line-height: 1.5;
    }
    </style>
    """, unsafe_allow_html=True)
    # 📄 Einleitung mit Spielrichtung
    st.markdown(f"""
    <div style='font-size: 1rem; line-height: 1.6;'>
        The following heatmaps show the aggregated movement patterns of both teams across the entire field. 
        Warm colors (e.g., <b>red</b>) indicate frequently visited zones, whereas <b>blue areas</b> indicate rarely visited zones.
        Below, you will find the attacking directions of both teams as well as an expandable section with guidance on how to interpret these heatmaps.
        <br>
        📌 <b>Team directions:</b><br>
        &emsp;▶️ <b>{team1['name']}</b>: <i>{dir1_text}</i><br>
        &emsp;◀️ <b>{team2['name']}</b>: <i>{dir2_text}</i>
        <br><br>
    </div>
    """, unsafe_allow_html=True)


    # 🔍 Interpretation im Expander
    with st.expander("🧠 Show heatmap interpretation"):
        st.markdown("""
        <div style='font-size:1rem; line-height:1.5;'>
            <ul style='padding-left: 1.2em; margin-top: 0.5em;'>
                <li><b>High activity in the right attacking third</b> (when playing <i>left → right</i>) may indicate <b>sustained pressure phases</b> or <b>frequent wing attacks</b>.</li>
                <li><b>Strong presence in the own penalty area</b> suggests <b>defensive behavior</b> or <b>opponent pressure phases</b>.</li>
                <li><b>Centered heatmaps</b> point to a <b>vertical, central attacking style</b>.</li>
                <li><b>Wing-heavy patterns</b> suggest <b>wide build-up play</b> or <b>half-space overloads</b>.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)




    # 📸 URLs zu den Heatmap-Bildern
    url_team1 = api_url(f"{session_id}/results/heatmaps/{team1['name']}")
    url_team2 = api_url(f"{session_id}/results/heatmaps/{team2['name']}")

    # 🔁 Bis zu 5 Versuche zum Laden der Heatmaps
    max_retries = 5
    success = False
    r1, r2 = None, None  # vorab definieren, damit auch nach der Schleife verfügbar

    for attempt in range(max_retries):
        r1 = requests.get(url_team1)
        r2 = requests.get(url_team2)

        if r1.status_code == 200 and r2.status_code == 200:
            print("✅ Heatmaps loaded successfully.")
            success = True
            break
        else:
            print(f"❌ Attempt {attempt+1} failed: Heatmaps not available yet.")
            sec = (attempt * 3) + 5
            time.sleep(1)
        

    # 🔨 Nur wenn nach 3 Versuchen keine Heatmaps gefunden wurden → Generieren
    if not success:
        print("🧠 Generating Heatmaps...")

        @st.cache_data(show_spinner="🧠 Generiere Heatmaps...")
        def trigger_heatmap_generation(session_id):
            url = api_url(f"{session_id}/results/heatmaps/generate")
            return requests.post(url, timeout=600)

        response = trigger_heatmap_generation(session_id)

        if response.status_code == 200:
            print("✅ Heatmap generation triggered.")
            r1 = requests.get(url_team1)
            r2 = requests.get(url_team2)
        else:
            print(f"⚠️ Heatmap generation failed! Status: {response.status_code}")

    # 🔢 Spalten zur Anzeige der beiden Team-Heatmaps
    col1, col2 = st.columns(2)


    # 🖼️ Team 1 Heatmap
    with col1:
        if r1.status_code == 200:
            image1 = Image.open(BytesIO(r1.content))
            direction_str = "Left → Right" if dir1 == "left_to_right" else "Left ← Right"
            st.image(image1, caption=f"Movement heatmap of {team1['name']} ({direction_str})", use_container_width=True)
        else:
            st.error("❌ Heatmap for Team 1 not found.")

    with col2:
        if r2.status_code == 200:
            image2 = Image.open(BytesIO(r2.content))
            direction_str = "Left → Right" if dir2 == "left_to_right" else "Left ← Right"
            st.image(image2, caption=f"Movement heatmap of {team2['name']} ({direction_str})", use_container_width=True)
        else:
            st.error("❌ Heatmap for Team 2 not found.")

    st.markdown("---")
    st.markdown("## 📊 Export KPI Data")
    st.write("")
    col1, middle, col2 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <a href="{api_url(f"{session_id}/results/metrics/excel")}" style="text-decoration: none;">
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
                    transition: background-color 0.2s ease;"
                    onmouseover="this.style.backgroundColor='#33333322'" 
                    onmouseout="this.style.backgroundColor='transparent'">
                    📈 <span>Download Excel</span>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )

    with middle:
        st.markdown(
            f"""
            <a href="{api_url(f"{session_id}/results/heatmaps/generate")}" style="text-decoration: none;">
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
                    transition: background-color 0.2s ease;"
                    onmouseover="this.style.backgroundColor='#33333322'" 
                    onmouseout="this.style.backgroundColor='transparent'">
                    🗺️ <span>Download Movement Maps</span>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <a href="{api_url(f"{session_id}/results/video")}" download style="text-decoration: none;">
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
                    transition: background-color 0.2s ease;"
                    onmouseover="this.style.backgroundColor='#33333322'" 
                    onmouseout="this.style.backgroundColor='transparent'">
                    📥 <span>Download Annotated Match Video</span>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")