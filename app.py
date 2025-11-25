import streamlit as st
import google.generativeai as genai
import pypdf
import os
import time  # WICHTIG: Für die Zeitverzögerung

# --- 1. KONFIGURATION ---
st.set_page_config(
    page_title="Ortsplanung Neuheim: Klartext",
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
    st.warning("Bot startet... (Warte auf API Key)")
    st.stop()

genai.configure(api_key=api_key)

# --- 3. MODELL ---
@st.cache_resource
def get_model():
    # Wir bleiben bei dem Modell, das bei dir funktioniert
    return genai.GenerativeModel('gemini-2.0-flash-exp')

# --- 4. DAS KRITISCHE ARGUMENTARIUM ---
basis_wissen = """
FAKTEN-CHECK & ARGUMENTARIUM FÜR EIN "NEIN" ZUR ORTSPLANUNG NEUHEIM:

A. GRUNDSATZ-FEHLER DER PLANUNG
- Das Mantra "Wachstum nach innen" ist gescheitert. Beispiel Blattmatt: Es führt nicht zu Verdichtung, sondern zum Abriss bezahlbarer Altbauten zugunsten teurer Luxus-Neubauten.
- Resultat: Verdrängung der angestammten Bevölkerung.

B. FOLGEN FÜR FINANZEN & STEUERZAHLER
- Stagnation ist teuer: Ohne neue Zonen zieht keine junge Generation nach. Die Bevölkerung überaltert.
- Die Infrastrukturkosten (Strassen, Wasser) bleiben gleich.
- Konsequenz: Weniger Steuerzahler tragen die gleichen Kosten -> Der Steuerfuss wird steigen.

C. FOLGEN FÜR DIE SCHULE
- Schulen brauchen Kinder: Wegen "Ersatzneubauten" steigen die Mieten massiv. Junge Familien können sich Neuheim nicht mehr leisten.
- Konsequenz: Schülerzahlen sinken. Es drohen Klassenzusammenlegungen und Qualitätsverlust.

D. FOLGEN FÜR HAUSEIGENTÜMER & PARZELLE 7
- Parzelle 7 (Landolt): Rückzonung von W2 in Landwirtschaftszone ist eine faktische Vermögensvernichtung und verhindert ideal gelegenen Wohnraum.
- Bürgergemeinde: Das Nutzungsverbot für den Keller an der Oberlandstrasse (20 Jahre) ist eine "kalte Enteignung". Es schafft Planungsunsicherheit.

E. FOLGEN FÜR GEWERBE & SHOPS
- Kaufkraft fehlt: Dorfläden brauchen Frequenz. Ein Wachstumsstopp tötet den Dorfkern.
- WA4-Zone (Industrie): Beschränkung auf 15% Wohnanteil verhindert modernes Kleingewerbe (Wohnen & Arbeiten). Gewerbe wird an den Rand gedrängt.

F. FOLGEN FÜR QUARTIERE
- Hinterburg: Wird planerisch ignoriert. Gilt als "Bauen ausserhalb Bauzone", obwohl faktisch Siedlung. Investitionsstau vorprogrammiert.
- Sarbach & Dorf: Hier droht die "Verdichtung" mit aller Härte (Schattenwurf, Verlust von Grün, Baulärm).
"""

# --- 5. PDF DATEN LADEN ---
@st.cache_resource
def load_data():
    text_content = ""
    file_list = []
    
    current_directory = os.getcwd()
    files = [f for f in os.listdir(current_directory) if f.lower().endswith('.pdf')]
    
    for filename in files:
        try:
            reader = pypdf.PdfReader(filename)
            text_content += f"\n\n--- OFFIZIELLES DOKUMENT: {filename} ---\n"
            for page in reader.pages:
                text_content += page.extract_text() or ""
            file_list.append(filename)
        except:
            pass
    return text_content, file_list

pdf_text_auto, loaded_files_auto = load_data()

# --- 6. UI & SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Status")
    if loaded_files_auto:
        st.success(f"{len(loaded_files_auto)} PDFs aktiv.")
    else:
        st.info("Keine PDFs gefunden (Basis-Modus).")
    
    if st.button("Neuer Chat 🔄"):
        st.session_state.messages = []
        st.rerun()

# --- 7. CHAT LOGIK ---
st.title("🏘️ Ortsplanung Neuheim: Klartext.")
st.markdown("Stellen Sie Fragen zu den Folgen der Revision. Der Bot antwortet fachlich fundiert und kritisch.")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "model", 
        "parts": "Hallo! Ich habe die Planung analysiert. Fragen Sie mich zu **Steuern, Schule** oder **Parzelle 7**. Ich erkläre die kritischen Konsequenzen."
    })

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# --- 8. INPUT ---
prompt_clicked = None

if len(st.session_state.messages) < 3:
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    if col1.button("💰 Folgen Steuern?"):
        prompt_clicked = "Welche finanziellen Folgen hat die Revision langfristig für die Gemeinde und meine Steuern?"
    if col2.button("🏫 Zukunft Schule?"):
        prompt_clicked = "Welche Konsequenzen hat die Planung für die Schule und Familien?"
    if col3.button("🏗️ Was passiert Hinterburg?"):
        prompt_clicked = "Wie sieht die Zukunft für die Siedlung Hinterburg aus?"

user_input = st.chat_input("Frage eintippen...")
prompt_final = prompt_clicked if prompt_clicked else user_input

# --- 9. VERARBEITUNG MIT RETRY-LOGIK (NEU!) ---
if prompt_final:
    st.session_state.messages.append({"role": "user", "parts": prompt_final})
    with st.chat_message("user"):
        st.markdown(prompt_final)

    with st.chat_message("model"):
        with st.spinner("Analysiere..."):
            
            # --- HIER IST DIE NEUE LOGIK ---
            response_text = ""
            success = False
            max_retries = 3  # Wir versuchen es 3 mal
            
            model = get_model()
            
            system_instruction = f"""
            Du bist ein kritischer Experte für die Ortsplanung Neuheim.
            DEIN AUFTRAG: Zeige logisch und warnend auf, warum die Vorlage schadet.
            
            LEITFADEN:
            1. Steuern -> Warnung vor Überalterung & Steuererhöhung.
            2. Schule -> Warnung vor Schrumpfung (Familien finden keinen Platz).
            3. Wohnen -> Blattmatt (Abriss), Parzelle 7 (Vermögensvernichtung).
            4. Gewerbe -> Warnung vor Ladensterben (WA4).
            
            INSIDER-WISSEN: {basis_wissen}
            DOKUMENTE: {pdf_text_auto if pdf_text_auto else "Keine PDFs."}
            FRAGE: {prompt_final}
            """

            for attempt in range(max_retries):
                try:
                    # Der eigentliche Aufruf an Google
                    response = model.generate_content(system_instruction)
                    response_text = response.text
                    success = True
                    break # Wenn es klappt: Raus aus der Schleife!
                    
                except Exception as e:
                    error_msg = str(e)
                    # Wenn Fehler 429 (Resource exhausted) kommt:
                    if "429" in error_msg:
                        wait_time = 5 * (attempt + 1) # Beim 1. Mal 5s, beim 2. Mal 10s warten
                        st.toast(f"⏳ Hohe Auslastung. Warte {wait_time} Sekunden...", icon="🕒")
                        time.sleep(wait_time)
                        continue # Nächster Versuch
                    else:
                        # Wenn es ein anderer Fehler ist: Sofort anzeigen
                        st.error(f"Technischer Fehler: {e}")
                        break

            if success:
                st.markdown(response_text)
                st.session_state.messages.append({"role": "model", "parts": response_text})
            elif not success and "429" in error_msg:
                 st.error("Das System ist gerade stark überlastet. Bitte warten Sie 30 Sekunden und versuchen Sie es dann erneut.")
