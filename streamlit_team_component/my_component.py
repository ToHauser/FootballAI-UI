# Datei: streamlit_team_component/my_component.py
import streamlit.components.v1 as components
import os

# Absoluter Pfad zur build-Directory
component_dir = os.path.join(os.path.dirname(__file__), "template", "my_component", "frontend", "build")

# Komponente deklarieren mit FIXEM Pfad
my_component_declaration = components.declare_component(
    "my_component",
    path=os.path.abspath(component_dir)
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
