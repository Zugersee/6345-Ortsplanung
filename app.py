import streamlit as st
import google.generativeai as genai
import pypdf
import os

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(
    page_title="Ortsplanung Neuheim: Der Check",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="collapsed" # Sidebar eingeklappt für Fokus auf Chat
)

# --- 2. SICHERHEIT & API KEY ---
# Der Bot holt sich den Schlüssel leise aus den Secrets.
# Nutzer sehen davon nichts.
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    # Nur für dich zum Testen, falls Secrets fehlen:
    with st.sidebar:
        st.warning("⚠️ Kein API Key in Secrets gefunden.")
        api_key = st.text_input("Notfall-Eingabe API Key", type="password")

if not api_key:
    st.error("Der Bot ist noch nicht konfiguriert (API Key fehlt).")
    st.stop()

genai.configure(api_key=api_key)

# --- 3. DAS MODELL ---
@st.cache_resource
def get_model():
    # Gemini 1.5 Flash ist ideal für grosse Textmengen (PDFs)
    return genai.GenerativeModel('gemini-1.5-flash')

# --- 4. DAS "INSIDER WISSEN" (Die kritische Stimme) ---
basis_wissen = """
KRITISCHE FAKTEN & HINTERGRÜNDE (Insider-Wissen):

1. WOHNRAUM & WACHSTUM
- Offizielle Doktrin: "Wachstum nach innen".
- Realität: In der 'Blattmatt' werden intakte Wohnhäuser abgerissen. Günstiger Wohnraum wird vernichtet.
- Konsequenz: Bezahlbarer Wohnraum entsteht fast nur auf der "grünen Wiese". Verdichtung (=Abriss & Neubau) treibt die Mietpreise hoch.

2. PARZELLE 7 (Landolt / Säntisstrasse)
- Plan: Rückzonung von W2 in Landwirtschaftszone.
- Kritik: Eine verpasste Chance. Die Fläche ist eben und ideal gelegen. Hier müsste W3 eingezont werden für bezahlbaren Wohnraum, statt Fläche zu streichen.

3. INDUSTRIE & GEWERBE (WA4-Zone)
- Mogelpackung: Heisst "Wohn-Arbeits-Zone", erlaubt aber nur 15% Wohnanteil.
- Folge: Verhindert lebendige Durchmischung. Ist eigentümerfeindlich. Unterstützt vom Hauseigentümerverband-Präsidium (Neuheimer Kantonsrat), was widersprüchlich ist.

4. FINANZEN & STEUERN
- Risiko: Wenn Wachstum verhindert wird (keine Neueinzonungen), fehlen langfristig neue Steuerzahler, um die Infrastruktur zu finanzieren.
- Bürgergemeinde: Der Keller an der Oberlandstrasse darf 20 Jahre nicht genutzt werden (faktische Enteignung, Wertverlust).

5. ÖFFENTLICHE BAUTEN & SCHULE
- Technikmuseum ZDT: Bleibt in Landwirtschaftszone, Zukunft unsicher (keine Umzonung in OeIB).
- Hinterburg: Kantonale Richtlinien passen nicht zur faktischen Siedlung. Kombistudie wurde verweigert.
"""

# --- 5. PDF LADER (Automatisch von GitHub + Manuell) ---
@st.cache_resource
def load_data():
    text_content = ""
    file_list = []
    
    # 1. Suche nach PDFs direkt im GitHub-Ordner
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

# Daten laden
pdf_text_auto, loaded_files_auto = load_data()

# --- 6. UI & SIDEBAR ---
with st.sidebar:
    st.header("📚 Quellen & Dokumente")
    
    # Anzeige was automatisch geladen wurde
    if loaded_files_auto:
        st.success(f"Integriert: {len(loaded_files_auto)} Dokumente von GitHub.")
        with st.expander("Liste ansehen"):
            for f in loaded_files_auto:
                st.write(f"- {f}")
    else:
        st.info("Keine PDFs auf GitHub gefunden. Nutze Insider-Wissen.")

    st.markdown("---")
    st.write("**Zusätzliche Dateien?**")
    uploaded_files = st.file_uploader("Hier PDFs reinziehen (optional)", type=["pdf"], accept_multiple_files=True)
    
    # Button zum Resetten
    if st.button("Unterhaltung neu starten 🗑️"):
        st.session_state.messages = []
        st.rerun()

# Text kombinieren (Auto + Manuell)
full_pdf_text = pdf_text_auto
if uploaded_files:
    for pdf in uploaded_files:
        reader = pypdf.PdfReader(pdf)
        full_pdf_text += f"\n\n--- MANUELLER UPLOAD: {pdf.name} ---\n"
        for page in reader.pages:
            full_pdf_text += page.extract_text() or ""

# --- 7. CHAT OBERFLÄCHE ---

st.title("🏘️ Ortsplanung Neuheim: Klartext.")
st.markdown("""
Willkommen. Hier erhalten Sie Antworten zu den **konkreten Auswirkungen** der Revision.
Der Bot vergleicht die offiziellen Pläne mit kritischen Fakten.
""")

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Begrüssungsnachricht des Bots
    st.session_state.messages.append({
        "role": "model", 
        "parts": "Hallo! Ich habe die Unterlagen analysiert. Fragen Sie mich etwas zu **Steuern, Schule, Bauzonen** oder den **finanziellen Folgen**."
    })

# Verlauf anzeigen
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# --- 8. VORSCHLAGS-BUTTONS (Um das Gespräch zu starten) ---
# Zeige Buttons nur, wenn noch keine User-Frage gestellt wurde (außer der Begrüßung)
if len(st.session_state.messages) < 2:
    st.markdown("Beispielfragen (einfach anklicken):")
    col1, col2, col3 = st.columns(3)
    prompt_clicked = None
    
    if col1.button("💰 Folgen für Steuerzahler?"):
        prompt_clicked = "Welche finanziellen Folgen hat die Revision langfristig für die Gemeinde und meine Steuern?"
    
    if col2.button("🏗️ Kann ich noch bauen?"):
        prompt_clicked = "Was bedeutet 'Wachstum nach innen' konkret für Bauherren? Gibt es Verlierer?"
        
    if col3.button("🏫 Zukunft der Schule?"):
        prompt_clicked = "Wie wirkt sich die Planung auf die Entwicklung der Schule und Familien aus?"

# --- 9. EINGABE & LOGIK ---
user_input = st.chat_input("Ihre eigene Frage hier eintippen...")

if prompt_clicked:
    prompt = prompt_clicked
else:
    prompt = user_input

if prompt:
    # 1. User Nachricht
    st.session_state.messages.append({"role": "user", "parts": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. KI Antwort
    with st.chat_message("model"):
        with st.spinner("Analysiere Dokumente und Fakten..."):
            try:
                model = get_model()
                
                system_instruction = f"""
                Du bist ein neutraler, aber kritischer Analyst für die Ortsplanung Neuheim.
                
                DEINE AUFGABE:
                Erkläre dem Bürger die Auswirkungen der Revision.
                Vergleiche dazu immer zwei Perspektiven:
                1. Die offizielle Planung (aus den PDF-Texten unten).
                2. Die kritische Realität / Insider-Wissen (aus dem Text unten).

                REGELN:
                - Sei verständlich für Laien.
                - Wenn nach **Finanzen/Steuern/Wirtschaft** gefragt wird: Suche Zahlen in den PDFs, aber warne vor den Risiken des Wachstums-Stopps (Insider-Wissen).
                - Wenn nach **Bauen** gefragt wird: Erkläre die Zonen (W2, WA4 etc.) und nenne konkrete Beispiele wie Blattmatt oder Parzelle 7.
                - Nenne Ross und Reiter (z.B. ZDT, Hinterburg, Bürgergemeinde).
                
                --- QUELLE 1: INSIDER WISSEN ---
                {basis_wissen}
                
                --- QUELLE 2: OFFIZIELLE DOKUMENTE ---
                {full_pdf_text if full_pdf_text else "Warnung: Keine PDFs geladen. Antworte nur basierend auf Insider-Wissen."}
                
                FRAGE DES BÜRGERS: {prompt}
                """
                
                response = model.generate_content(system_instruction)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "model", "parts": response.text})
                
            except Exception as e:
                st.error(f"Ein Fehler ist aufgetreten: {e}")
