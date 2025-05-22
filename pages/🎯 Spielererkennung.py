import streamlit as st
import time
import requests
from config import API_BASE

st.set_page_config(
    page_title="Fortschritt | FootballAI",
    page_icon="⚽",
    layout="wide"
)

session_id = st.session_state.get("session_id")
if not session_id:
    st.error("Keine Session aktiv.")
    st.stop()
if "active_session" in st.session_state:
    del st.session_state["active_session"]

st.title("🎬 Tracking läuft...")
st.write("")
st.markdown(f"**📁 Session-ID:** `{session_id}`")
st.info("🔐 Bitte notiere dir diese Session-ID, um später wieder auf das Ergebnis zugreifen zu können.")

progress_bar = st.progress(0, text="Initialisiere Tracking...")

progress_data = {"current": 0, "total": 1}
team_frames_ready = False

def check_progress():
    try:
        r = requests.get(f"{API_BASE}/progress/{session_id}", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[WARN] Fortschrittsabruf fehlgeschlagen: {e}")
    return {"current": 0, "total": 1}

def check_team_frames():
    try:
        r = requests.get(f"{API_BASE}/team-frames/{session_id}", timeout=5)
        return r.status_code == 200
    except Exception as e:
        print(f"[WARN] Team-Frames noch nicht verfügbar: {e}")
        return False

last_update = time.time()
while True:
    now = time.time()
    if now - last_update >= 5:  # Nur alle 2 Sekunden GET-Anfragen
        progress_data = check_progress()
        last_update = now

    current = progress_data["current"]
    total = progress_data["total"]
    pct = current / total if total > 0 else 0
    progress_bar.progress(pct, text=f"Fortschritt: {int(pct * 100)}%")

    if current >= total:
        if check_team_frames():
            st.success("✅ Tracking abgeschlossen & Zuweisungsdaten verfügbar. Weiterleitung...")
            time.sleep(2)
            st.switch_page("pages/👥 Team Zuweisung.py")
            break

    time.sleep(0.5)
