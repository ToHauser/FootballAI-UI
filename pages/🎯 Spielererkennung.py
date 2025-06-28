import streamlit as st
import time
import requests
from config import API_BASE

# === Konfiguration ===
st.set_page_config(page_title="Fortschritt | FootballAI", page_icon="⚽", layout="wide")

session_id = st.session_state.get("session_id")
if not session_id:
    st.error("❌ Keine Session aktiv.")
    st.stop()

st.title("🎬 Fortschritt")
st.markdown(f"**📁 Session-ID:** `{session_id}`")
st.info("🔐 Notiere dir diese ID, um später auf das Ergebnis zuzugreifen.")

st.session_state.pop("active_session", None)  # Zurücksetzen falls vorhanden

# === UI-Platzhalter ===
phase_header = st.empty()
progress_bar = st.progress(0, text="Initialisiere Tracking...")

# === API-Helper ===
def check_progress(mode):
    try:
        r = requests.get(f"{API_BASE}/progress/{mode}/{session_id}", timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[WARN] Fortschritt ({mode}) nicht abrufbar: {e}")
    return {"current": 0, "total": 1}

def check_session_info():
    try:
        r = requests.get(f"{API_BASE}/session-info/{session_id}", timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[WARN] Session-Info nicht abrufbar: {e}")
    return {}

def check_team_frames():
    try:
        r = requests.get(f"{API_BASE}/team-frames/{session_id}", timeout=10)
        return r.status_code == 200
    except Exception:
        return False

# === Initialstatus abfragen
session_info = check_session_info()
tracking_ready = session_info.get("tracking_exists", False)
transformer_ready = session_info.get("view_exists", False)

# === Schneller Exit bei abgeschlossenem Prozess
if tracking_ready and transformer_ready and check_team_frames():
    if st.session_state.get("automatic_assignment"):
        st.success("✅ Automatische Teamzuweisung abgeschlossen. Weiterleitung...")
        st.session_state["redirect_to_only_video_download"] = False
        time.sleep(2)
        st.switch_page("pages/🧠 Metrik Analyse.py")
    else:
        st.success("✅ Tracking & Transformation abgeschlossen. Weiterleitung...")
        time.sleep(2)
        st.switch_page("pages/👥 Team Zuweisung.py")
    st.stop()

# === Modus: Tracking abgeschlossen, Transformation läuft
if tracking_ready and not transformer_ready:
    phase_header.markdown("### 🧭 Starte Spielfeld-Transformation...")
    while True:
        session_info = check_session_info()
        transformer_ready = session_info.get("view_exists", False)

        if transformer_ready:
            st.session_state["automatic_assignment"] = True
            st.success("✅ Transformation abgeschlossen. Weiterleitung...")
            time.sleep(5)
            st.switch_page("pages/👥 Team Zuweisung.py")
            st.stop()

        progress = check_progress("transformer")
        pct = progress["current"] / progress["total"] if progress["total"] > 0 else 0
        progress_bar.progress(pct, text=f"View Transformation: {int(pct * 100)}%")
        time.sleep(0.5)

# === Modus: Tracking läuft noch
phase_header.markdown("### 🔄 Tracking läuft...")
in_tracking_phase = True
transformer_announced = False

while True:
    session_info = check_session_info()
    tracking_ready = session_info.get("tracking_exists", False)
    transformer_ready = session_info.get("view_exists", False)

    if in_tracking_phase:
        progress = check_progress("tracking")
        pct = progress["current"] / progress["total"] if progress["total"] > 0 else 0
        progress_bar.progress(pct, text=f"Tracking: {int(pct * 100)}%")

        if tracking_ready:
            in_tracking_phase = False
            transformer_announced = False
            progress_bar.progress(0, text="Initialisiere View Transformation...")

    else:
        if not transformer_announced:
            phase_header.markdown("### 🧭 Starte Spielfeld-Transformation...")
            transformer_announced = True

        progress = check_progress("transformer")
        pct = progress["current"] / progress["total"] if progress["total"] > 0 else 0
        progress_bar.progress(pct, text=f"View Transformation: {int(pct * 100)}%")

        if transformer_ready and check_team_frames():
            st.success("✅ Tracking & Transformation abgeschlossen. Weiterleitung...")
            time.sleep(5)
            st.switch_page("pages/👥 Team Zuweisung.py")
            st.stop()

    time.sleep(0.5)
