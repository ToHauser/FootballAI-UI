import os
import requests
import streamlit as st
# config.py


SESSION_ROOT = "../FootballAI_Backend/sessions"  # relativer Pfad zum Backend

API_BASE_PATH = "/api/v1/sessions"


def get_api_base():
    return st.secrets.get("API_BASE", os.getenv("API_BASE", "http://localhost:8000"))