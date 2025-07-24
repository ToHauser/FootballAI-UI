import json
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
from PIL import Image
import requests
import base64
import io
import config 
from streamlit_team_component.my_component import my_component


st.set_page_config(
    page_title="Team Assignment | FootballAI",
    page_icon="⚽",
    layout="wide"
)
if "active_session" in st.session_state:
    del st.session_state["active_session"]


API_BASE = st.secrets["API_BASE"] if "API_BASE" in st.secrets else os.getenv("API_BASE", "http://localhost:8000")
def api_url(endpoint: str) -> str:
    return f"{API_BASE.rstrip('/')}{config.API_BASE_PATH.rstrip('/')}/{endpoint.lstrip('/')}"

# Session-ID laden
session_id = st.session_state.get("session_id", None)

if not session_id:
    st.warning("⚠️ Keine Session-ID gefunden.")
    st.stop()

if st.session_state.get("automatic_assignment", False):
    st.session_state["redirect_to_only_video_download"] = False
    st.switch_page("pages/🧠 Metrik Analyse.py")

# Warten bis Backend die Teamzuweisung vorbereitet hat
with st.spinner("Warte auf Abschluss der Teamzuweisungs-Vorbereitung..."):
    for attempt in range(40):  # max. 20 Versuche = 100 Sekunden
        try:
            r = requests.get(api_url(f"{session_id}"))
            if r.status_code == 200:
                info = r.json()
                if info.get("assignment_notification_exists"):
                    break
        except Exception as e:
            print(f"Fehler bei session-info Abruf: {e}")
        time.sleep(10)
    else:
        st.error("❌ Teamzuweisung noch nicht bereit. Bitte später erneut versuchen.")
        st.stop()


# Frames laden 
with st.spinner("Lade Teamzuweisungsdaten..."):
    frames = []
    team_config = {}
    for attempt in range(10):
        try:
            r = requests.get(api_url(f"{session_id}/team-assignment/frames"), timeout=10)

            if r.status_code == 200:
                response_data = r.json()
                frames = response_data.get("frames", [])
                team_config = response_data.get("team_config", {})
                if frames:
                    break  # Erfolg
        except Exception as e:
            print(f"⚠️ Versuch {attempt + 1}: Fehler beim Laden – {e}")
        time.sleep(2)

    if not frames:
        st.error("❌ Teamframes konnten nicht geladen werden. Bitte Backend prüfen.")
        st.stop()


# Farben & Namen definieren
team_colors = {
    "1": team_config.get("1", {}).get("color", "#FF0000"),
    "2": team_config.get("2", {}).get("color", "#0000FF"),
    "removed": "#777777"
}
team_names = {
    "1": team_config.get("1", {}).get("name", "Team 1"),
    "2": team_config.get("2", {}).get("name", "Team 2")
}

# 🧠 Session-State vorbereiten
st.session_state.setdefault("team_assignments", {})
st.session_state.setdefault("frame_index", 0)
st.session_state.setdefault("framewise_assignments", {})
st.session_state.setdefault("latest_assignments", None)

# Aktueller Frame
frame_index = st.session_state["frame_index"]
current = frames[frame_index]

# Bild vorbereiten
image_data = base64.b64decode(current["image"])
image = Image.open(io.BytesIO(image_data)).convert("RGB")
width, height = image.size
buffered = io.BytesIO()
image.save(buffered, format="PNG")
img_b64 = base64.b64encode(buffered.getvalue()).decode()

# Spieler vorbereiten
for player in current["players"]:
    pid = str(player["id"])
    team = str(player.get("team", "1"))  # automatisch zugewiesenes Team oder Default "1"
    if pid not in st.session_state["team_assignments"]:
        st.session_state["team_assignments"][pid] = {
            "team": team,
            "removed": False,
            "bbox": player["bbox"]
        }


# Initialwerte laden
framewise = st.session_state["framewise_assignments"]
assignments = framewise.get(str(frame_index), {
    pid: {
        "team": st.session_state["team_assignments"][pid]["team"],
        "removed": st.session_state["team_assignments"][pid]["removed"]
    }
    for pid in st.session_state["team_assignments"]
})

# 🏷️ Titel mit Teamnamen und Farbkacheln
st.markdown(f"""
<h2 style='margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.6rem;'>
  Team Assignment für
  <span style='display: inline-flex; align-items: center;'>
    <span style='width: 16px; height: 16px; background-color: {team_colors['1']}; border-radius: 50%; display: inline-block; margin-right: 4px; vertical-align: middle;'></span>
    {team_names['1']}
  </span>
  vs.
  <span style='display: inline-flex; align-items: center;'>
    <span style='width: 16px; height: 16px; background-color: {team_colors['2']}; border-radius: 50%; display: inline-block; margin-right: 4px; vertical-align: middle;'></span>
    {team_names['2']}
  </span>
</h2>
""", unsafe_allow_html=True)
st.write("")
st.markdown(f"**📁 Session-ID:** `{session_id}`")
st.write("")
# 📘 Beschreibung zur Steuerung
st.markdown(f"""
<div style='margin-bottom: 1.5rem; font-size: 0.95rem;'>
  Auf dieser Seite legen Sie die <strong>Spielrichtung</strong> sowie die <strong>Teamzuweisung</strong> der Spieler fest.
  Dies ermöglicht eine präzisere Analyse und Erkennung relevanter Spielmetriken.<br><br>
  Durch einen <b>Klick</b> auf eine Person wird diese dem Team <b>{team_names['2']}</b> 
  <span style='display: inline-block; width: 12px; height: 12px; background-color: {team_colors['2']}; border-radius: 3px; margin-left: 6px;'></span> zugewiesen.<br>
  Ein erneuter Klick weist diese wieder <b>{team_names['1']}</b> 
  <span style='display: inline-block; width: 12px; height: 12px; background-color: {team_colors['1']}; border-radius: 3px; margin-left: 6px;'></span> zu.<br><br>
  Gelegentlich können Personen wie Schiedsrichter fälschlich als Spieler erkannt worden sein. 
  Mit <b>Shift + Klick</b> markieren Sie diese als "kein Spieler" (grau dargestellt).
</div>
""", unsafe_allow_html=True)


display_width = 1050
scale = display_width / width
respone_global = None

# Navigation Buttons oberhalb des Frames (funktional)
st.markdown(f"<div style='width: {display_width}px;'>", unsafe_allow_html=True)
col1, col_mid, col2 = st.columns([1, 1, 1])
with col1:
    if st.button("⬅️ Zurück", key="top_back") and frame_index > 0:
        st.session_state["frame_index"] -= 1
        st.rerun()
# Speichern
with col2:
    if frame_index == len(frames) - 1:
        if st.button("✅ Zuweisung speichern"):
            if st.session_state["latest_assignments"]:
                st.session_state["framewise_assignments"][str(frame_index)] = st.session_state["latest_assignments"]
                for pid, values in st.session_state["latest_assignments"].items():
                    st.session_state["team_assignments"][pid]["team"] = values["team"]
                    st.session_state["team_assignments"][pid]["removed"] = values["removed"]

            payload = {
                "players": st.session_state["team_assignments"],
            }
            
            response = requests.post(api_url(f"{session_id}/team-assignment/save-manual"), json=payload)
            respone_global = response.status_code

with col2:
    if frame_index != len(frames) - 1:
        if st.button("Weiter ➡️", key="top_next") and frame_index < len(frames) - 1:
            if st.session_state["latest_assignments"]:
                st.session_state["framewise_assignments"][str(frame_index)] = st.session_state["latest_assignments"]
                for pid, values in st.session_state["latest_assignments"].items():
                    st.session_state["team_assignments"][pid]["team"] = values["team"]
                    st.session_state["team_assignments"][pid]["removed"] = values["removed"]
            st.session_state["frame_index"] += 1
            st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

if respone_global != None and respone_global == 200:
    st.success("✅ Team Assignment erfolgreich gespeichert. Bitte warten Sie auf das Video...")
    st.session_state["redirect_to_only_video_download"] = False
    time.sleep(2.0)
    st.switch_page("pages/🧠 Metrik Analyse.py")  # 🔄 neue Seite
elif respone_global != None and respone_global != 200:
    st.error(f"❌ Fehler beim Speichern: {respone_global}. Bitte erneut versuchen.")

# React-Komponente
latest_result = my_component(
    image=img_b64,
    players=current["players"],
    assignments=assignments,
    colors=team_colors,
    width=width,
    height=height,
    scale=scale,  # 👈 NEU
    key=f"frame_{frame_index}"
)


if latest_result is not None:
    st.session_state["latest_assignments"] = latest_result

