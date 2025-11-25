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
    
    # Ihre verfügbaren Modelle in strategischer Reihenfolge:
    priority_queue = [
        # 1. Das "Gehirn" (Beste Argumentation)
        'gemini-2.0-pro-exp-02-05',
        
        # 2. Der "neue Sprinter" (Sehr schnell & modern)
        'gemini-2.5-flash',
        
        # 3. Der "Klassiker" (Sehr stabil)
        'gemini-2.0-flash',
        
        # 4. Der "Notnagel" (Lite Version, kaum Limits)
        'gemini-2.0-flash-lite'
    ]

    last_error = None

    # Status-Container für den User (damit er sieht, was passiert)
    status_placeholder = st.empty()

    for model_name in priority_queue:
        try:
            # Kurzes Feedback welches Modell gerade probiert wird (optional)
            # status_placeholder.caption(f"Versuche Modell: {model_name}...")
            
            # Modell laden
            model = genai.GenerativeModel(model_name)
            
            # Generieren
            response = model.generate_content(prompt_text)
            
            # Erfolg! Platzhalter leeren und Ergebnisse zurückgeben
            status_placeholder.empty()
            return response.text, model_name
            
        except Exception as e:
            # Fehler speichern
            last_error = e
            # Wenn es ein "Rate Limit" (429) oder "Overloaded" (503) ist, kurz warten
            if "429" in str(e) or "503" in str(e):
                time.sleep(1) # Kurze Atempause
            continue # Nächstes Modell in der Liste probieren
    
    # Wenn ALLE Modelle scheitern:
    status_placeholder.error("Alle Modelle sind derzeit überlastet.")
    raise last_error

# --- 4. DAS BASIS-WISSEN (Ihr Argumentarium) ---
basis_wissen = """
FAKTEN-CHECK & ARGUMENTARIUM "NEIN" ZUR ORTSPLANUNG NEUHEIM:

A. GRUNDSATZ-FEHLER
- "Wachstum nach innen" (Bsp. Blattmatt) führt real zu Abriss günstiger Altbauten für teure Neubauten.
- Resultat: Verdrängung der Bevölkerung statt Verdichtung.

B. FINANZEN & STEUERN
- Stagnation = Überalterung. Infrastrukturkosten bleiben gleich bei weniger Zahlern.
- Konsequenz: Steuererhöhung ist vorprogrammiert.

C. SCHULE
- Ersatzneubauten sind zu teuer für junge Familien. Zuzug fehlt.
- Konsequenz: Schülerzahlen sinken, Klassenabbau droht.

D. PARZELLE 7 & EIGENTUM
- Rückzonung Parzelle 7 (W2->Landwirtschaft) vernichtet Vermögen und verhindert idealen Wohnraum.
- Bürgergemeinde: Nutzungsverbot Keller Oberlandstrasse (20 Jahre) = kalte Enteignung.

E. GEWERBE
- WA4-Zone (nur 15% Wohnen) verhindert modernes Kleingewerbe.
- Ladensterben droht wegen fehlender Kaufkraft (Stagnation).

F. HINTERBURG
- Wird ignoriert. Gilt als "ausserhalb Bauzone", obwohl faktisch Siedlung. Investitionsstau.
"""

# --- 5. PDF LADEN ---
@st.cache_resource
def load_data():
    text = ""
    files_found = []
    current_dir = os.getcwd()
    files = [f for f in os.listdir(current_dir) if f.lower().endswith('.pdf')]
    for f in files:
        try:
