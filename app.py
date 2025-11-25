import streamlit as st
import google.generativeai as genai
import pypdf
import os

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
    # Fallback für lokales Testen
    if "api_key_input" not in st.session_state:
        st.session_state.api_key_input = "" 
    with st.sidebar:
        api_key = st.text_input("API Key (falls nicht in Secrets)", type="password")

if not api_key:
    st.warning("Bot startet... (Warte auf API Key)")
    st.stop()

genai.configure(api_key=api_key)

# --- 3. MODELL (UPDATE AUF 2.0) ---
@st.cache_resource
def get_model():
    # Nutzung des neuen Gemini 2.0 Flash Modells
    return genai.GenerativeModel('gemini-2.0-flash')

# --- 4. DAS KRITISCHE ARGUMENTARIUM (Basis-Wissen) ---
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
    st.header("⚙️ Steuerung")
    if loaded_files_auto:
        st.success(f"{len(loaded_files_auto)} offizielle PDFs geladen.")
    else:
        st.info("Keine PDFs auf GitHub gefunden (Nutze Argumentarium).")
    
    # Reset Button für den Notfall
    if st.button("Neuer Chat / Reset 🔄"):
        st.session_state.messages = []
        st.rerun()

# --- 7. CHAT LOGIK ---
st.title("🏘️ Ortsplanung Neuheim: Klartext.")
st.markdown("Stellen Sie Fragen zu den Folgen der Revision. Der Bot antwortet fachlich fundiert und kritisch.")

# History initialisieren
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "model", 
        "parts": "Hallo! Ich habe die Planung analysiert. Fragen Sie mich zu **Steuern, Schule, Hinterburg** oder den **finanziellen Risiken**. Ich sage Ihnen, was im Bericht steht - und was es wirklich bedeutet."
    })

# Verlauf anzeigen
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# --- 8. VORSCHLAGS-BUTTONS & INPUT ---

# Variable initialisieren
prompt_clicked = None

# Buttons nur zeigen, wenn der Chat noch frisch ist
if len(st.session_state.messages) < 3:
    st.markdown("---")
    st.markdown("**Beispielfragen:**")
    col1, col2, col3 = st.columns(3)
    
    if col1.button("💰 Folgen für Steuerzahler?"):
        prompt_clicked = "Welche finanziellen Folgen hat die Revision langfristig für die Gemeinde und meine Steuern?"
    
    if col2.button("🏫 Zukunft der Schule?"):
        prompt_clicked = "Welche Konsequenzen hat die Planung für die Schule und Familien?"
        
    if col3.button("🏗️ Was passiert in der Hinterburg?"):
        prompt_clicked = "Wie sieht die Zukunft für die Siedlung Hinterburg aus?"

# Eingabefeld
user_input = st.chat_input("Ihre kritische Frage hier eintippen...")

# Entscheidung: Button oder Tippen?
prompt_final = prompt_clicked if prompt_clicked else user_input

# --- 9. VERARBEITUNG ---
if prompt_final:
    # 1. User Nachricht anzeigen
    st.session_state.messages.append({"role": "user", "parts": prompt_final})
    with st.chat_message("user"):
        st.markdown(prompt_final)

    # 2. KI Antwort generieren
    with st.chat_message("model"):
        with st.spinner("Analysiere Fakten & Argumente (Gemini 2.0)..."):
            try:
                model = get_model()
                
                # Der scharfe System-Prompt
                system_instruction = f"""
                Du bist ein kritischer Experte für die Ortsplanung Neuheim.
                
                DEIN AUFTRAG:
                Zeige dem Bürger logisch, faktenbasiert und warnend auf, warum die Vorlage der Gemeinde schadet.
                
                ARGUMENTATIONS-LEITFADEN:
                1. Frage nach **Steuern/Finanzen** -> Warnung vor Überalterung & Steuererhöhung (weil Zahler fehlen).
                2. Frage nach **Schule** -> Warnung vor Schrumpfung (weil Familien verdrängt werden).
                3. Frage nach **Wohnen/Bauen** -> Nenne "Blattmatt" (Abriss statt Verdichtung) und "Parzelle 7" (Vermögensvernichtung).
                4. Frage nach **Gewerbe** -> Warnung vor Ladensterben und schlechter WA4-Zone.
                
                INSIDER-WISSEN (Deine Basis):
                {basis_wissen}
                
                OFFIZIELLE DOKUMENTE (Zum Widerlegen):
                {pdf_text_auto if pdf_text_auto else "Keine PDFs. Argumentiere rein aus dem Insider-Wissen."}
                
                FRAGE: {prompt_final}
                
                ANTWORT:
                Fachlich, konkret, "Ross und Reiter" nennend. Schließe mit einem klaren Fazit aus Sicht der Betroffenen.
                """
                
                response = model.generate_content(system_instruction)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "model", "parts": response.text})
                
            except Exception as e:
                # Fehlerbehandlung
                st.error(f"Ein technischer Fehler ist aufgetreten: {e}")
                st.info("Tipp: Prüfen Sie, ob der API Key Zugriff auf 'gemini-2.0-flash' hat.")
