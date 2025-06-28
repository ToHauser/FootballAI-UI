import os
import requests
import streamlit as st
# config.py
#API_BASE = "https://pest-berry-competitors-timothy.trycloudflare.com"


SESSION_ROOT = "../02_FootballAI/sessions"  # relativer Pfad zum Backend

def get_api_base():
    return st.secrets.get("API_BASE", os.getenv("API_BASE", "http://localhost:8000"))