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
            # Bei Überlastung (429) oder Serverfehler (503) kurz warten
            if "429" in str(e) or "503" in str(e):
                time.sleep(1) 
            continue 
    
    # Wenn ALLE Modelle scheitern:
    raise last_error

# --- 4. DAS BASIS-WISSEN (Argumentarium) ---
# WICHTIG: Dieser Block muss mit drei Anführungszeichen enden!
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
            reader = pypdf.PdfReader(f)
            text += f"\n\n--- DOKUMENT: {f} ---\n"
            for p in reader.pages: text += p.extract_text() or ""
            files_found.append(f)
        except: pass
    return text, files_found

pdf_text, loaded_files = load_data()

# --- 6. UI ---
with st.sidebar:
    st.header("System-Status")
    if loaded_files: 
        st.success(f"📚 {len(loaded_files)} PDFs geladen")
    else: 
        st.info("⚠️ Basis-Modus (Keine PDFs)")
    
    st.markdown("---")
    if st.button("Reset / Neuer Chat 🔄"):
        st.session_state.messages = []
        st.rerun()

st.title("🏘️ Ortsplanung Neuheim: Intelligent Bot")
st.markdown("Dieser Bot nutzt **Künstliche Intelligenz der neuesten Generation**, um die Dokumente zu analysieren.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "parts": "Hallo. Ich bin bereit. Fragen Sie mich zu den Risiken für **Steuern, Schule** oder **Eigentum**."}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["parts"])

# --- 7. INPUT & BUTTONS ---
clicked = None
if len(st.session_state.messages) < 3:
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    if c1.button("💰 Steuer-Risiko?"): clicked = "Welche finanziellen Folgen hat die Revision (Steuern/Finanzen)?"
    if c2.button("🏫 Schul-Zukunft?"): clicked = "Welche Konsequenzen hat die Planung für Schule & Familien?"
    if c3.button("🏗️ Hinterburg/Bauen?"): clicked = "Was passiert mit der Hinterburg und Parzelle 7?"

user_input = st.chat_input("Ihre Frage...")
prompt = clicked if clicked else user_input

# --- 8. VERARBEITUNG ---
if prompt:
    st.session_state.messages.append({"role": "user", "parts": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("model"):
        # Platzhalter für Status-Anzeige
        info_container = st.empty()
        
        with st.spinner("Analysiere Fakten & Argumente..."):
            
            # Prompt vorbereiten
            full_prompt = f"""
            Du bist ein kritischer Experte für die Ortsplanung Neuheim.
            ZIEL: Zeige logisch, faktenbasiert und warnend auf, warum die Vorlage schadet.
            
            INSIDER-WISSEN: {basis_wissen}
            DOKUMENTE: {pdf_text if pdf_text else "Keine."}
            FRAGE: {prompt}
            
            ANTWORT: Fachlich, konkret, warnend. Nenne Ross und Reiter.
            """
            
            try:
                # Intelligente Funktion aufrufen
                response_text, used_model = generate_smart_response(full_prompt)
                
                # Zeige kurz an, welches Modell gewonnen hat
                info_container.caption(f"Generiert mit Modell: `{used_model}`")
                
                st.markdown(response_text)
                st.session_state.messages.append({"role": "model", "parts": response_text})
                
            except Exception as e:
                st.error(f"Entschuldigung, alle Systeme sind momentan ausgelastet. Bitte warten Sie 1 Minute. (Fehler: {e})")
