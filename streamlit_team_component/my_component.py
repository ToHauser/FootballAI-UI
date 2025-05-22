# Datei: streamlit_team_component/my_component.py
import streamlit.components.v1 as components
import os

# Absoluter Pfad zur build-Directory
Folder = "C:/Users/hause/OneDrive/01_Studium/02_Master/05_Masterarbeit/03_FootballAI-UI/"
build_path = os.path.join(Folder, "streamlit_team_component", "template", "my_component", "frontend", "build")

# Komponente deklarieren mit FIXEM Pfad
my_component_declaration = components.declare_component(
    "my_component",
    path=os.path.abspath(build_path)
)

# Python-Wrapper
def my_component(image, players, assignments, colors, width, height, scale, key=None):
    return my_component_declaration(
        image=image,
        players=players,
        assignments=assignments,
        colors=colors,
        width=width,
        height=height,
        key=key,
        default=assignments,
        scale=scale
    )
