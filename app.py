import streamlit as st
import google.generativeai as genai
import pypdf
from io import BytesIO

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Neuheim Analyse Bot", page_icon="🏘️", layout="wide")

# --- 2. API KEY SETUP (CLOUD & LOKAL) ---
# Der Bot schaut erst in die geheimen Cloud-Settings. Wenn dort nichts ist, fragt er den User.
api_key = None

if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    # Fallback: Wenn jemand den Code lokal testet ohne Secrets
    if "api_key_input" not in st.session_state:
        st.session_state.api_key_input = ""
    
    with st.sidebar:
        st.warning("Kein API Key in den Secrets gefunden.")
        api_key = st.text_input("Google API Key eingeben", type="password")

if not api_key:
    st.info("Bitte API Key konfigurieren um zu starten.")
    st.stop()

genai.configure(api_key=api_key)

# --- 3. DAS "GEHEIME" INSIDER-WISSEN ---
basis_wissen = """
KRITISCHE ANALYSE / HINTERGRUNDWISSEN ZUR LAGE NEUHEIM:

1. WACHSTUMS-LÜGE & WOHNRAUM
- Offizielle Linie: "Wachstum nur nach innen".
- Realität: In der 'Blattmatt' werden zwei Wohnhäuser mit intakter Bausubstanz abgerissen. Günstiger Wohnraum wird vernichtet.
- Fazit: Bezahlbarer Wohnraum entsteht nur bei Neueinzonungen (Grüne Wiese), da Verdichtung durch Abriss/Neubau zu teuren Mieten führt.

2. PARZELLE 7 (Landolt / Säntisstrasse)
- Status: War W2, soll Landwirtschaftszone werden (Rückzonung).
- Kritik: Die Fläche ist eben und liegt ideal bis zum Hügelfuss Hirschleten. Hier müsste man W3 einzonen für bezahlbaren Wohnraum, statt rückzuzonen.

3. INDUSTRIEGEBIET (WA4-Zone)
- Etikettenschwindel: Heisst "Wohn-Arbeits-Zone", erlaubt aber nur 15% Wohnanteil.
- Kritik: Das verhindert lebendige Durchmischung. Eigentümerfeindlich. Ein Neuheimer Kantonsrat (Hauseigentümerverband-Präsidium!) stützt dies unverständlicherweise.

4. BÜRGERGEMEINDE
- Problem: Sandgefüllter Keller an der Oberlandstrasse.
- Folge: Darf wohl 20 Jahre nicht genutzt werden. Kommt einer Enteignung gleich.

5. TECHNIKMUSEUM ZDT & HINTERBURG
- ZDT: Liegt in Landwirtschaftszone, Zukunft ungesichert. Umzonung in OeIB verpasst.
- Hinterburg: Kanton sagt, Richtlinien für "Bauen ausserhalb Bauzone" passen hier nicht (da faktisch Siedlung). Planer (R+K) hatten "keine Lust" auf Kombistudie. Chance vertan.
"""

# --- 4. FUNKTIONEN ---
@st.cache_resource
def get_model():
    return genai.GenerativeModel('gemini-1.5-flash')

def extract_text_from_pdf(uploaded_files):
    text_content = ""
    for pdf_file in uploaded_files:
        try:
            pdf_reader = pypdf.PdfReader(pdf_file)
            text_content += f"\n\n--- DOKUMENT: {pdf_file.name} ---\n"
            for page in pdf_reader.pages:
                text_content += page.extract_text() or ""
        except Exception as e:
            st.error(f"Fehler beim Lesen von {pdf_file.name}: {e}")
    return text_content

# --- 5. UI & LOGIK ---
st.title("🏘️ Ortsplanung Neuheim: Fakten-Check")
st.markdown("""
**Anleitung für Texterinnen:**
1. Lade links die offiziellen PDFs hoch (Erläuterungsbericht, Zonenplan).
2. Stelle rechts kritische Fragen. Der Bot vergleicht die **offiziellen Aussagen** mit dem **Insider-Wissen**.
""")

# PDF Upload Handling
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

with st.sidebar:
    st.header("1. Wissen laden")
    uploaded_files = st.file_uploader("Offizielle PDFs hier ablegen", type=["pdf"], accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("PDFs verarbeiten"):
            with st.spinner("Lese Dokumente..."):
                st.session_state.pdf_text = extract_text_from_pdf(uploaded_files)
                st.success(f"{len(uploaded_files)} Dokumente integriert!")

    st.markdown("---")
    if st.button("Chat leeren 🗑️"):
        st.session_state.messages = []
        st.rerun()

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Begrüssung
if not st.session_state.messages:
    st.info("👋 Ich bin bereit. Lade PDFs hoch für Details zu Steuern/Schule oder frag direkt los zum Thema Zoneneinteilung.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# Input
if prompt := st.chat_input("Frage z.B.: Was bedeutet die Revision für meine Steuern?"):
    # 1. User Nachricht anzeigen
    st.session_state.messages.append({"role": "user", "parts": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. KI Antwort generieren
    with st.chat_message("model"):
        with st.spinner("Analysiere Quellen..."):
            try:
                model = get_model()
                
                # Prompt Engineering: Klare Anweisung für Faktencheck
                system_instruction = f"""
                Du bist ein kritischer Analyst für die Ortsplanung Neuheim.
                
                DEINE AUFGABE:
                Beantworte die Frage des Nutzers. Kombiniere dazu zwei Wissensquellen:
                1. OFFIZIELLE DOKUMENTE (Text aus PDFs, falls vorhanden). Hier stehen Details zu Steuern, Schule, Finanzen.
                2. KRITISCHES INSIDER-WISSEN (siehe unten). Hier stehen die wahren Probleme (Blattmatt, Parzelle 7, etc.).
                
                WICHTIG:
                - Wenn nach **Finanzen/Steuern** gefragt wird: Suche die Antwort primär in den PDFs. Wenn keine PDFs da sind, sage ehrlich: "Dazu brauche ich den Erläuterungsbericht (bitte hochladen)."
                - Wenn nach **Bauzonen/Projekten** gefragt wird: Nutze das Insider-Wissen, um Widersprüche zur offiziellen Lesart aufzuzeigen.
                - Sei konkret: Nenne Zahlen, Orte und Konsequenzen.
                - Tonalität: Sachlich, aufklärend, investigativ.
                
                --- QUELLE 1: INSIDER WISSEN ---
                {basis_wissen}
                
                --- QUELLE 2: PDF INHALT ---
                {st.session_state.pdf_text[:50000] if st.session_state.pdf_text else "LEER (Noch keine PDFs hochgeladen)"}
                
                FRAGE DES NUTZERS: {prompt}
                """
                
                response = model.generate_content(system_instruction)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "model", "parts": response.text})
                
            except Exception as e:
                st.error(f"Ein Fehler ist aufgetreten: {e}")
