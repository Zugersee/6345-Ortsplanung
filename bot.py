import streamlit as st
import google.generativeai as genai
import pypdf
from io import BytesIO

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Neuheim Analyse Bot", page_icon="🏘️", layout="wide")

# --- 2. API KEY SETUP ---
# Wir holen den Key sicherheitshalber aus der Seitenleiste, damit er nicht im Code stehen muss
with st.sidebar:
    st.header("🔑 Zugang")
    api_key = st.text_input("Google API Key eingeben", type="password")
    st.markdown("[Hier API Key holen](https://aistudio.google.com/)")

if not api_key:
    st.warning("Bitte gib links deinen Google API Key ein.")
    st.stop()

# Modell konfigurieren
genai.configure(api_key=api_key)

# --- 3. DAS "GEHEIME" INSIDER-WISSEN ---
# Dieser Text ist fest im Bot verankert. Er repräsentiert die kritische Sicht.
basis_wissen = """
KRITISCHE ANALYSE / HINTERGRUNDWISSEN ZUR LAGE:
1. Allgemeines Wachstum: Die Gemeinde behauptet, Wachstum sei nur nach innen möglich. Das ist eine politische Entscheidung, keine geologische.
   - Konsequenz Praxis: In der 'Blattmatt' werden zwei Wohnhäuser mit intakter Bausubstanz abgerissen. Das vernichtet günstigen Wohnraum.
   - Konsequenz Markt: Echter bezahlbarer Wohnraum entsteht meist nur bei Neueinzonungen (Grüne Wiese), da Verdichtung im Bestand teuer ist (Abriss/Neubau).

2. Parzelle 7 (Landolt / Säntisstrasse):
   - Status: War bisher W2-Zone.
   - Plan: Soll in Landwirtschaftszone zurück-gezont werden.
   - Kritik: Das ist eine ebene Fläche bis zum Hügelfuss der Hirschleten. Es wäre sinnvoller, dies als W3-Zone einzuzonen, um dringend benötigten, bezahlbaren Wohnraum zu schaffen.

3. Industriegebiet (WA4-Zone):
   - Problem: Der Name "Wohn-Arbeits-Zone" täuscht.
   - Restriktion: Der Wohnanteil ist auf mickrige 15% beschränkt.
   - Konsequenz: Das ist eigentümerfeindlich. Es bleibt zu wenig Platz zum Wohnen. Ein Neuheimer Kantonsrat (Präsidium Hauseigentümerverband) unterstützt dies unverständlicherweise.

4. Bürgergemeinde Neuheim:
   - Problem: Besitzt einen sandgefüllten Kellerraum an der Oberlandstrasse.
   - Konsequenz: Darf diesen aufgrund der Planung wohl die nächsten 20 Jahre nicht nutzen/leersaugen. Enteignung durch die Hintertür?

5. Technikmuseum ZDT:
   - Status: Liegt in der Landwirtschaftszone. Zukunft ungesichert.
   - Versäumnis: Eine Umzonung in die OeIB-Zone (Zone für öffentliche Bauten) wurde verpasst.

6. Siedlung Hinterburg:
   - Konflikt: Kantonale Raumplanung sagt, Richtlinien für "Bauen ausserhalb Bauzone" passen hier nicht, da es faktisch eine Siedlung ist (4 MFH, 5 Gewerbe, 2 EFH).
   - Versäumnis: Herr Hutter bot Mitarbeit an. Das Planungsbüro R+K hatte "keine Lust" auf eine Kombistudie. Chance vertan.
"""

# --- 4. HILFSFUNKTIONEN ---
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
st.title("🏘️ Ortsplanung Neuheim: Analyse-Tool")
st.markdown("""
**Ziel:** Verstehe die wahren Konsequenzen der Revision.
Dieser Bot vergleicht die **offiziellen Dokumente** (bitte hochladen) mit **kritischem Insider-Wissen**.
""")

# PDF Upload Handling
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

with st.sidebar:
    st.header("📄 Offizielle Dokumente")
    st.info("Lade hier Erläuterungsbericht, Zonenplan etc. hoch.")
    uploaded_files = st.file_uploader("PDFs hier ablegen", type=["pdf"], accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("Dokumente analysieren"):
            with st.spinner("Lese Dokumente..."):
                st.session_state.pdf_text = extract_text_from_pdf(uploaded_files)
                st.success("Wissen integriert!")

    if st.button("Chat zurücksetzen"):
        st.session_state.messages = []
        st.rerun()

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# Input
if prompt := st.chat_input("Stelle eine kritische Frage..."):
    # 1. User Nachricht anzeigen
    st.session_state.messages.append({"role": "user", "parts": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. KI Antwort generieren
    with st.chat_message("model"):
        with st.spinner("Analysiere Konsequenzen..."):
            try:
                model = get_model()
                
                # Der System-Prompt wird bei jedem Aufruf neu gebaut, um sicherzugehen, 
                # dass PDF-Inhalt und Basis-Wissen kombiniert sind.
                
                system_instruction = f"""
                Du bist ein kritischer Analyst für die Ortsplanung Neuheim.
                
                DEINE AUFGABE:
                Beantworte die Frage des Nutzers, indem du zwei Quellen vergleichst:
                1. OFFIZIELLE SICHT (aus den hochgeladenen PDFs).
                2. KRITISCHE SICHT / REALITÄT (aus dem untenstehenden Insider-Wissen).
                
                DEIN STIL:
                - Sei konkret. Nenne Orte, Zonen und Zahlen.
                - Zeige Konsequenzen auf ("Das bedeutet für Sie...").
                - Deck Widersprüche auf. Wenn der offizielle Bericht "Qualität" sagt, aber "Abriss" meint, sag das.
                - Bleib sachlich, aber schonungslos offenlegend.
                
                --- QUELLE 1: KRITISCHES INSIDER WISSEN ---
                {basis_wissen}
                
                --- QUELLE 2: INHALT DER HOCHGELADENEN PDFS ---
                {st.session_state.pdf_text if st.session_state.pdf_text else "Noch keine PDFs hochgeladen. Nutze vorerst nur das Insider-Wissen."}
                
                --- ENDE QUELLEN ---
                
                FRAGE DES NUTZERS: {prompt}
                """
                
                # Sende den kompletten Kontext als "Prompt" (Stateless approach für RAG)
                response = model.generate_content(system_instruction)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "model", "parts": response.text})
                
            except Exception as e:
                st.error(f"Ein Fehler ist aufgetreten: {e}")
