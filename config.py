import requests

def get_current_ngrok_url():
    try:
        r = requests.get("http://127.0.0.1:4040/api/tunnels")
        tunnels = r.json()["tunnels"]
        https_tunnel = next((t for t in tunnels if t["proto"] == "https"), None)
        return https_tunnel["public_url"] if https_tunnel else None
    except Exception as e:
        print(f"❌ Fehler beim Abrufen der Ngrok-URL: {e}")
        return None

def write_to_env_file(url):
    with open(".env", "w") as f:
        f.write(f"API_BASE={url}\n")
    print(f"✅ .env-Datei aktualisiert mit: {url}")

if __name__ == "__main__":
    ngrok_url = get_current_ngrok_url()
    if ngrok_url:
        write_to_env_file(ngrok_url)
    else:
        print("⚠️ Keine Ngrok-URL gefunden.")

# config.py
API_BASE = "https://brakes-recent-nested-willow.trycloudflare.com"

SESSION_ROOT = "../02_FootballAI/sessions"  # relativer Pfad zum Backend
