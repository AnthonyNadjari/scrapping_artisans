"""
Page Facturation - Gestion des factures avec Excel comme source de vérité
"""
import streamlit as st
import sys
from pathlib import Path

# Configuration de la page
st.set_page_config(page_title="Facturation", page_icon="📄", layout="wide")

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from facturation.streamlit_page import render_facturation_page

# Afficher la page
render_facturation_page()

