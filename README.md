# FootballAI Frontend

The **FootballAI Frontend** is a Streamlit-based user interface for the FootballAI system.  
It provides an interactive environment for uploading videos, assigning teams, running tactical analysis, and visualizing spatio-temporal match metrics.

---

## ⚠️ Important Note

This frontend must be used **together with** the [FootballAI Backend](https://github.com/ToHauser/FootballAI_Backend).  
Both must be placed inside the same parent directory:

## 📂 Recommended Directory Structure

```plaintext
FootballAI/                 # Main folder
├── FootballAI_Backend/     # Clone from backend repo
└── FootballAI_Frontend/          # Clone from frontend repo
```

## 🚀 Getting Started

1. **Clone the frontend repository**
   ```bash
   git clone https://github.com/ToHauser/FootballAI_UI.git
   cd FootballAI_UI
    ```
2. **Create and activate a virtual environment**
    ```bash
    python -m venv venv
    source venv/bin/activate   # Linux/Mac
    venv\Scripts\activate      # Windows
    ```

3. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
4. **Run the Backend**
    The frontend will automatically connect to the backend if started via the backend's start.bat script.
