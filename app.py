import streamlit as st
import google.generativeai as genai
import pypdf
import os
import time

# --- 1. KONFIGURATION ---
st.set_page_config(
    page_title="Ortsplanung Neuheim: Intelligent Bot",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. API KEY SETUP ---
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    if "api_key_input" not in st.session_state:
        st.session_state.api_key_input = "" 
    with st.sidebar:
        api_key = st.text_input("API Key", type="password")

if not api_key:
    st.warning("Bitte API Key eingeben.")
    st.stop()

genai.configure(api_key=api_key)

# --- 3. DIE INTELLIGENTE MODELL-AUSWAHL (DIE KASKADE) ---
def generate_smart_response(prompt_text):
    """
    Versucht Modelle nach 'Leistung' -> 'Geschwindigkeit' -> 'Sicherheit'.
    """
    
    # Hier ist die Reihenfolge der Modelle, die probiert werden:
    priority_queue = [
        'gemini-2.0-pro-exp-02-05',  # 1. Das "Gehirn" (Beste Argumentation)
        'gemini-2.5-flash',          # 2. Der "neue Sprinter" (Sehr schnell)
        'gemini-2.0-flash',          # 3. Der "Klassiker" (Stabil)
        'gemini-2.0-flash-lite'      # 4. Der "Notnagel" (Kaum Limits)
    ]

    last_error = None
    status_placeholder = st.empty()

    for model_name in priority_queue:
        try:
            # Modell laden
            model = genai.GenerativeModel(model_name)
            
            # Generieren
            response = model.generate_content(prompt_text)
            
            # Erfolg! 
            return response.text, model_name
            
        except Exception as e:
            last_error = e
            # Bei Überlastung kurz warten und nächstes Modell probieren
            if "429" in str(e) or "503" in str(e):
                time.sleep(1) 
            continue 
    
    # Wenn ALLE Modelle scheitern:
    raise last_error

# --- 4. DAS BASIS-WISSEN (Argumentarium) ---
basis_wissen = """
FAKTEN-CHECK & ARGUMENTARIUM "NEIN" ZUR ORTSPLANUNG NEUHEIM:

A. GRUNDSATZ-FEHLER
- "Wachstum nach innen" (Bsp. Blattmatt) führt real zu Abriss günstiger Altbauten für teure Neubauten.
- Resultat: Verdrängung der Bevölkerung statt Verdichtung.

B.
