import streamlit as st
import google.generativeai as genai
import pypdf
import os
import time

# --- 1. KONFIGURATION ---
st.set_page_config(
    page_title="Ortsplanung Neuheim: Turbo Check",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. API KEY ---
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

# --- 3. MODELL (TURBO-PRIORITÄT) ---
def generate_fast_response(prompt_text):
    # Wir nutzen die schnellsten Modelle zuerst
    priority_queue = [
        'gemini-2.5-flash',
        'gemini-2.0-flash',
        'gemini-2.0-flash-lite'
    ]
    
    last_error = None
    for model_name in priority_queue:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt_text)
            return response.text, model_name
        except Exception as e:
            last_error = e
            time.sleep(0.5)
            continue
            
    raise last_error

# --- 4. DAS BASIS-WISSEN (KRITIK) ---
basis_wissen_kritik = """
FAKTEN-CHECK & ARGUMENTARIUM "NEIN" ZUR ORTSPLANUNG NEUHEIM (Kritische Haltung):

1. SCHULE & FAMILIEN:
- "Ersatzneubauten" führen zu hohen Mieten -> Verdrängung junger Familien -> Schülerschwund -> Klassenabbau.

2. WIRTSCHAFT & GEWERBE:
- WA4-Zone erlaubt nur 15% Wohnanteil. Das verhindert modernes Kleingewerbe (Wohnen & Arbeiten).
- Gewerbe wird an den Rand gedrängt.

3. BLATTMATT (WOHNEN):
- "Wachstum nach innen" bedeutet hier: Abriss intakter, günstiger Häuser für Luxus-Neubau.

4. HINTERBURG:
- Wird planerisch ignoriert (gilt als "ausserhalb Bauzone", ist aber Siedlung). Investitionsstau.

5. STEUERN & FINANZEN:
- Stagnation = Überalterung. Infrastrukturkosten bleiben gleich -> Steuererhöhung droht.

6. DORF & SARBACH:
- Verdichtung mit der Brechstange: Verlust von Gärten, Schattenwurf, Baulärm.
"""

# --- 5. DER OFFIZIELLE BERICHT (FEST INTEGRIERT) ---
# Dieser Text ist sofort verfügbar (ohne Ladezeit!)
offizieller_bericht_text = """
Gemeinde Neuheim, Ortsplanungsrevision, Ausscheidung Gewässerräume.
Erläuterungsbericht zur Festlegung der Gewässerräume nach Art. 47 RPV.

ZUSAMMENFASSUNG DER WICHTIGSTEN PUNKTE AUS DEM BERICHT:
1. Ausgangslage: Anpassung an revidiertes Gewässerschutzgesetz (GSchG). Innerhalb und ausserhalb Bauzonen müssen Gewässerräume festgelegt werden.
2. Bauverbot: Im Gewässerraum gilt grundsätzlich Bauverbot.
3. Abstand: Innerhalb Bauzone 6m, ausserhalb 9m (wenn kein GWR festgelegt).
4. Spezialfall Sarbach (Gebiet Erlenbach): Verzicht auf GWR im Bereich der Eindolung (Hofareal), da Offenlegung den Landwirtschaftsbetrieb einschränken würde (Interessenabwägung).
5. Spezialfall Sihl (Sihlbrugg): Gewässerraum 78m. Im Bereich Bebauungsplan reduziert (dicht überbautes Gebiet), um Erweiterung Gewerbe/Tankstelle nicht zu verunmöglichen.
6. Stehende Gewässer: GWR für Hinterburgmüli Weiher und Baggersee Hinterthan festgelegt (Naturschutz).
7. Lorze: Gewässerraum ca. 70m (basierend auf natürlicher Sohlenbreite 40m). Im Bereich Höllgrotten zurückgestellt wegen laufender Planung.
8. Hinterburgmülibach: Teilweise GWR festgelegt (Hochwassergefahr), teilweise verzichtet.
9. Baarburgbach: Teilweise GWR festgelegt (Naturschutzgebiet).
10. Konsequenzen: Wo GWR festgelegt ist, ist die Nutzung eingeschränkt (Bauverbot, nur extensive Bewirtschaftung).
"""

# --- 6. PDF LADEN (OPTIONAL & MANUELL) ---
def get_additional_pdf_text():
    # Prüfen, ob der User manuell was hochgeladen hat
    uploaded_files = st.session_state.get('uploaded_pdfs', [])
    text = ""
    if uploaded_files:
        for pdf_file in uploaded_files:
            try:
                reader = pypdf.PdfReader(pdf_file)
                text += f"\n\n--- ZUSATZ-PDF: {pdf_file.name} ---\n"
                for page in reader.pages:
                    text += page.extract_text() or ""
            except:
                pass
    return text

# --- 7. UI ---
st.title("🏘️ Ortsplanung Neuheim: Fakten-Check")

# SIDEBAR MIT WARNUNG
with st.sidebar:
    st.header("📂 Zusatz-Dokumente")
    st.info("Der Bot kennt den 'Erläuterungsbericht Gewässerräume' bereits auswendig!")
    
    st.markdown("---")
    st.write("**Weitere PDFs hinzufügen?**")
    st.warning("⚠️ Achtung: Das Hochladen von PDFs führt zu Wartezeiten bei der Antwort!")
    
    files = st.file_uploader("PDFs hier ablegen", type=["pdf"], accept_multiple_files=True, key="uploaded_pdfs")
    
    if st.button("Reset 🔄"):
        st.session_state.messages = []
        st.rerun()

st.markdown("Klicken Sie auf ein Thema, um die **wahren Konsequenzen** zu erfahren.")

# --- 8. DAS 6-BUTTON MENÜ ---
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = None

col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)

prompt_clicked = None

# Reihe 1
if col1.button("🏫 Schule / Familien", use_container_width=True):
    prompt_clicked = "Welche negativen Konsequenzen hat die Planung konkret für die Schule und junge Familien?"

if col2.button("💼 Wirtschaft / Gewerbe", use_container_width=True):
    prompt_clicked = "Was bedeutet die WA4-Zone und die Planung für das lokale Gewerbe und die Wirtschaft?"

if col3.button("🏗️ Blattmatt / Wohnen", use_container_width=True):
    prompt_clicked = "Was passiert in der Blattmatt? Warum führt 'Wachstum nach innen' dort zu Abriss?"

# Reihe 2
if col4.button("🏚️ Hinterburg", use_container_width=True):
    prompt_clicked = "Wie wird die Siedlung Hinterburg in der Planung behandelt und welche Nachteile hat das?"

if col5.button("💰 Steuern / Finanzen", use_container_width=True):
    prompt_clicked = "Warum drohen Steuererhöhungen und welche finanziellen Risiken birgt die Stagnation?"

if col6.button("🌊 Gewässer / Sihl / Lorze", use_container_width=True):
    prompt_clicked = "Was bedeutet der 'Erläuterungsbericht Gewässerräume' für Eigentümer an der Sihl, Lorze oder am Sarbach? Wo gibt es Bauverbote?"

# --- CHATVERLAUF ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if prompt_clicked:
    st.session_state.messages.append({"role": "user", "parts": prompt_clicked})
    st.session_state.must_respond = True

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# --- EINGABE & VERARBEITUNG ---
user_input = st.chat_input("Eigene Frage stellen...")

if user_input:
    st.session_state.messages.append({"role": "user", "parts": user_input})
    st.session_state.must_respond = True
    with st.chat_message("user"):
        st.markdown(user_input)

if st.session_state.get("must_respond", False):
    last_user_msg = st.session_state.messages[-1]["parts"]
    
    # Text zusammenbauen
    additional_pdf_text = get_additional_pdf_text()
    
    with st.chat_message("model"):
        info = st.empty()
        with st.spinner("Analysiere..."):
            
            full_prompt = f"""
            Du bist ein kritischer Experte für die Ortsplanung Neuheim.
            ZIEL: Zeige dem Bürger logisch, faktenbasiert und warnend auf, warum die Vorlage schadet oder was sie bedeutet.
            
            TEIL 1: KRITISCHES BASIS-WISSEN (Argumentarium):
            {basis_wissen_kritik}
            
            TEIL 2: OFFIZIELLER BERICHT GEWÄSSERRÄUME (Fest integriert):
            {offizieller_bericht_text}
            
            TEIL 3: ZUSÄTZLICHE PDFS (Falls vom User hochgeladen):
            {additional_pdf_text if additional_pdf_text else "Keine zusätzlichen PDFs."}
            
            FRAGE: {last_user_msg}
            
            ANTWORT: Fachlich, konkret, warnend. Beziehe dich auf den Gewässerbericht, wenn nach Bächen/Flüssen gefragt wird.
            """
            
            try:
                response_text, used_model = generate_fast_response(full_prompt)
                
                # Feedback an User
                quellen_info = "Basiswissen + Gewässerbericht"
                if additional_pdf_text:
                    quellen_info += " + Externe PDFs"
                info.caption(f"⚡ Analyse basierend auf: {quellen_info}")
                
                st.markdown(response_text)
                st.session_state.messages.append({"role": "model", "parts": response_text})
                st.session_state.must_respond = False
                
            except Exception as e:
                st.error(f"Fehler: {e}. Bitte noch einmal versuchen.")
                st.session_state.must_respond = False
