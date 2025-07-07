import os
import uuid
import streamlit as st
from streamlit.components.v1 import html
import requests
import time
import config
import streamlit as st
from config import API_BASE_PATH

st.set_page_config(
    page_title="Startseite | FootballAI",
    page_icon="⚽",
    layout="wide"
)

if st.session_state.get("redirect_to_team_assignment"):
    st.session_state["redirect_to_team_assignment"] = False  # einmalig
    st.switch_page("pages/👥 Team Zuweisung.py")  # nur möglich mit multipage setup


st.title("⚽ Football Video Analyzer")

API_BASE = st.secrets["API_BASE"] if "API_BASE" in st.secrets else os.getenv("API_BASE", "http://localhost:8000")

def api_url(endpoint: str) -> str:
    return f"{API_BASE.rstrip('/')}{API_BASE_PATH.rstrip('/')}/{endpoint.lstrip('/')}"

SESSION_ROOT = config.SESSION_ROOT  # relativer Pfad zum Backend

st.markdown("---")

# --- 🔎 Session ID Zugriff
st.subheader("🔍 Existierende Session analysieren")
st.write("Sofern bereits eine Analyse durchgeführt wird, bekommst du darin eine Session-ID. Mithilfe dieser ID kannst du auf die Ergebnisse dieser zugreifen.")
with st.expander("Session-ID eingeben und fortfahren", expanded=True):
    session_input = st.text_input("Session-ID eingeben")

    if st.button("📂 Öffne Session"):
        if not session_input:
            st.warning("Bitte eine Session-ID eingeben.")
        else:
            st.session_state["active_session"] = session_input  # merken

# Verarbeite bekannte Session
if "active_session" in st.session_state:
    session_id = st.session_state["active_session"]
    r = requests.get(api_url(f"{session_id}"))
    tracking_exists = False
    assign_exists = False
    annotated_exists = False
    team_config = None

    if r.status_code == 200:
        info = r.json()
        tracking_exists = info["tracking_exists"]
        view_exists = info["view_exists"]
        assign_exists = info["assign_exists"]
        annotated_exists = info["annotated_exists"]
        team_config = info["team_config"]

    else:
        st.error(f"❌ Session-Infos konnten nicht geladen werden: {r.text}")

    st.markdown("### 📄 Vorhandene Artefakte:")
    st.write(f"🎯 Tracking Log: {'✅' if tracking_exists else '❌'}")
    st.write(f"🧭 Spielfeld Kalibrierung: {'✅' if view_exists else '❌'}")
    st.write(f"👥 Team Zuweisung: {'✅' if assign_exists else '❌'}")
    st.write(f"🎬 Annotiertes Video: {'✅' if annotated_exists else '❌'}")

    if not tracking_exists and not assign_exists and not annotated_exists:
        st.error(f"❌ Session-Infos konnten nicht geladen werden.")

    if tracking_exists and not view_exists and team_config:
        if st.button("🧭 Spielfeld kalibrieren"):
            st.session_state["run_view_transformation"] = True

            if st.session_state.get("run_view_transformation", False):
                with st.spinner("Generiere Spielfeldkalibrierung..."):
                    payload = {
                        "session_id": session_id,
                        "team1_name": team_config["1"]["name"],
                        "team1_color": team_config["1"]["color"],
                        "team2_name": team_config["2"]["name"],
                        "team2_color": team_config["2"]["color"],
                        "run_automatic_assignment": False,
                        "run_manual_assignment": True,
                    }
                    r = requests.post(f"{API_BASE}/annotate_only", data=payload)

                    if r.status_code == 200:
                        st.session_state["session_id"] = session_id
                        st.session_state["automatic_assignment"] = False
                        st.switch_page("pages/🎯 Spielererkennung.py")
                    else:
                        st.error(f"❌ Fehler bei der Annotierung: {r.text}")
                    

    # ▶️ Team Assignment starten
    if tracking_exists and view_exists and not assign_exists and team_config:
        if st.button("➡️ Starte Team Assignment"):
            st.session_state["run_assignment"] = True

    if st.session_state.get("run_assignment", False):
        with st.spinner("Starte Teamzuweisung..."):
            payload = {
                "session_id": session_id,
                "team1_name": team_config["1"]["name"],
                "team1_color": team_config["1"]["color"],
                "team2_name": team_config["2"]["name"],
                "team2_color": team_config["2"]["color"],
                "run_automatic_assignment": False,
                "run_manual_assignment": True,
            }
            st.session_state["run_manual_assignment"] = True
            st.session_state["run_assignment"] = False

            r = requests.post(f"{API_BASE}/annotate_only", data=payload)
            time.sleep(3)
            if r.status_code == 200:
                # Setze Redirect-Flag und leite weiter
                st.session_state["redirect_to_team_assignment"] = True
                st.session_state["redirect_to_only_video_download"] = False
                st.session_state["session_id"] = session_id
                st.switch_page("pages/👥 Team Zuweisung.py")
            else:
                st.error(f"❌ Fehler: {r.text}")
            del st.session_state["run_assignment"]

    # ▶️ Annotiertes Video erzeugen
    if tracking_exists and view_exists and assign_exists and not annotated_exists and team_config:
        if st.button("🎬 Video annotieren"):
            st.session_state["run_annotate"] = True

            if st.session_state.get("run_annotate", False):
                with st.spinner("Erstelle annotiertes Video..."):
                    payload = {
                        "session_id": session_id,
                        "team1_name": team_config["1"]["name"],
                        "team1_color": team_config["1"]["color"],
                        "team2_name": team_config["2"]["name"],
                        "team2_color": team_config["2"]["color"],
                        "run_automatic_assignment": False,
                        "run_manual_assignment": True,
                    }
                    r = requests.post(f"{API_BASE}/annotate_only", data=payload)

                    if r.status_code == 200:
                        st.session_state["session_id"] = session_id
                        st.session_state["redirect_to_only_video_download"] = False

                        st.switch_page("pages/🧠 Metrik Analyse.py")
                    else:
                        st.error(f"❌ Fehler bei der Annotierung: {r.text}")
                    del st.session_state["run_annotate"]
    elif tracking_exists and view_exists and assign_exists and annotated_exists and team_config:
        if st.button("🎬 Ergebnisse ansehen"):
            st.session_state["session_id"] = session_id
            st.session_state["redirect_to_only_video_download"] = True
            st.switch_page("pages/🧠 Metrik Analyse.py")
    

st.markdown("---")

# --- 🆕 Neue Session starten
st.subheader("🆕 Neue Analyse starten")
st.write("")  # eine Leerzeile
st.write("")  # eine Leerzeile

st.markdown("<p style='font-size:25px;'>🔧 Teamkonfiguration</p>", unsafe_allow_html=True)
st.markdown("""
<p style='font-size:16px; color:white;'>
Bitte gib hier die <strong>Teamkürzel</strong> (z. B. <em>VFB</em> für VFB Stuttgart) und die zugehörigen <strong>Teamfarben</strong> an.
<br>
Diese Angaben helfen bei der späteren <strong>eindeutigen Zuordnung</strong> von Spielern im Spielverlauf.
</p>
""", unsafe_allow_html=True)

col1a, col1b = st.columns([1, 4])
with col1a:
    team1_color = st.color_picker("1. Teamfarbe", value="#0000FF")
with col1b:
    team1_name = st.text_input("1. Teamkürzel (3 Buchstaben)", value="VFB").upper()
if len(team1_name) > 3:
    team1_name = team1_name[:3]
    st.warning("⚠️ Nur die ersten 3 Buchstaben werden übernommen.")

col2a, col2b = st.columns([1, 4])
with col2a:
    team2_color = st.color_picker("2. Teamfarbe", value="#FF0000")
with col2b:
    team2_name = st.text_input("2. Teamkürzel (3 Buchstaben)", value="FCB").upper()
if len(team2_name) > 3:
    team2_name = team2_name[:3]
    st.warning("⚠️ Nur die ersten 3 Buchstaben werden übernommen.")

st.write("")  # eine Leerzeile
st.write("")  # eine Leerzeile
st.write("")  # eine Leerzeile

st.markdown("<p style='font-size:25px;'>🎥 Halbzeit-Video bereitstellen</p>", unsafe_allow_html=True)
st.markdown("""
<p style='font-size:16px; color:white;'>
Hier kannst du ein <strong>kurzes Video</strong> (z. B. ein Halbzeitausschnitt von wenigen Minuten) hochladen.
<br>
Alternativ kannst du im Falle größerer Dateien auch einen <strong>Direktlink</strong> zu einer Online-Quelle angeben – wichtig ist, dass der Link direkt auf eine <code>.mp4</code>-Datei verweist (z. B. <code>https://example.com/video.mp4</code>).
</p>
""", unsafe_allow_html=True)

st.write("")  # eine Leerzeile

upload_method = st.radio("Wie möchtest du dein Video bereitstellen?", ["Upload", "Cloud-Link (GoogleDrive & DropBox empfohlen)"])

video_file = None
cloud_link = None

if upload_method == "Upload":
    video_file = st.file_uploader("🎞️ MP4-Datei hochladen", type=["mp4"])
    st.info("Bitte lade **nur eine Halbzeit** als MP4 hoch. Optimale Größe: <200MB.")
else:
    cloud_link = st.text_input("🔗 Freigabelink einfügen (z. B. Google Drive, DropBox) - OneDrive wird nicht unterstützt!")
    st.warning("⚠️ Stelle sicher, dass der Link öffentlich zugänglich ist und direkt auf das Video verweist.")

# -- Run-Optionen
if video_file or cloud_link:
    # Session-State initialisieren, wenn nicht vorhanden
    if "run_assignment" not in st.session_state:
        st.session_state["run_assignment"] = True
    if "run_manual_assignment" not in st.session_state:
        st.session_state["run_manual_assignment"] = False

    def toggle_auto():
        st.session_state["run_assignment"] = True
        st.session_state["run_manual_assignment"] = False

    def toggle_manual():
        st.session_state["run_manual_assignment"] = True
        st.session_state["run_assignment"] = False

    col1, col2 = st.columns(2)

    with col1:
        st.checkbox(
            "Automatische Teamzuweisung",
            key="run_assignment",
            on_change=toggle_auto
        )

    with col2:
        st.checkbox(
            "Manuelle Teamzuweisung",
            key="run_manual_assignment",
            on_change=toggle_manual
        )

    if st.button("🚀 Analyse starten"):
        with st.spinner("Video wird heruntergeladen..."):
            payload = {
                "team1_name": team1_name,
                "team1_color": team1_color,
                "team2_name": team2_name,
                "team2_color": team2_color,
                "run_tracking": True,
                "run_automatic_assignment": st.session_state.run_assignment and not st.session_state.run_manual_assignment,
                "run_manual_assignment": st.session_state.run_manual_assignment and not st.session_state.run_assignment,
            }

            try:
                if st.session_state.run_assignment:
                    st.session_state["automatic_assignment"] = True

                if cloud_link:
                    payload["video_url"] = cloud_link
                    if "session_id" in st.session_state:
                        del st.session_state["session_id"]
                    st.session_state["session_id"] = f"{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
                    
                    payload["session_id"] = st.session_state.get("session_id")                 
                    r = requests.post(api_url(f"{session_id}/video-from-link"), json=payload, headers={"accept": "application/json"})
                    if r.status_code != 200:
                        print("❌ Upload-Fehler:", r.text)
                        try:
                            error_msg = r.json().get("message", r.text)
                        except Exception:
                            error_msg = r.text

                        st.error(f"❌ {error_msg}")
                    else:
                        st.info(f"📁 Session-ID: `{payload['session_id']}`")
                        time.sleep(5)
                        st.switch_page("pages/🎯 Spielererkennung.py")
                else:
                    if "session_id" in st.session_state:
                        del st.session_state["session_id"]
                    
                    st.session_state["session_id"] = f"{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
                    
                    files = {"file": (video_file.name, video_file, "video/mp4")}
                    r = requests.post(api_url(f"{session_id}/video"), files=files, data=payload, headers={"accept": "application/json"})
                    if r.status_code != 200:
                        print("❌ Upload-Fehler:", r.text)
                        try:
                            error_msg = r.json().get("message", r.text)
                        except Exception:
                            error_msg = r.text

                        st.error(f"❌ {error_msg}")

                    else:
                        st.info(f"📁 Session-ID: `{payload['session_id']}`")
                        time.sleep(5)
                        st.switch_page("pages/🎯 Spielererkennung.py")                

            except Exception as e:
                print(f"❌ Ausnahmefehler beim Upload: {e}")  