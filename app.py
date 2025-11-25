import streamlit as st
import google.generativeai as genai
import pypdf
import os
import time

# --- 1. KONFIGURATION ---
st.set_page_config(
    page_title="Ortsplanung Neuheim: Fakten-Check",
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

# --- 4. BASIS-WISSEN (KRITISCHE FAKTEN, SACHLICH FORMULIERT) ---
basis_wissen_kritik = """
FAKTEN-CHECK & HINTERGRÜNDE ZUR ORTSPLANUNG NEUHEIM:

1. SCHULE & FAMILIEN:
- Fakt: Die Planung setzt auf "Ersatzneubauten". Dies führt marktüblich zu höheren Mietpreisen im Vergleich zum Bestand.
- Demografische Auswirkung: Für junge Familien wird der Zuzug erschwert. Dies hat direkten Einfluss auf die Entwicklung der Schülerzahlen und langfristig auf die Klassenbestände.

2. WIRTSCHAFT & GEWERBE (WA4-Zone):
- Fakt: Der Wohnanteil in der Zone WA4 ist auf 15% begrenzt.
- Auswirkung: Diese Quote limitiert die Ansiedlung von Kleingewerbe, das Wohnen und Arbeiten kombinieren möchte. Gewerbetreibende werden tendenziell in reine Arbeitszonen gelenkt.

3. BLATTMATT (WOHNEN):
- Planungsziel: "Wachstum nach innen".
- Realität vor Ort: In der Blattmatt bedeutet dies den Ersatz von bestehender Bausubstanz durch Neubauten. Dies verändert die Preisstruktur des Wohnraums erheblich und führt zu einer Veränderung der Bewohnerstruktur (Verdrängungseffekt).

4. HINTERBURG:
- Status: Die Siedlung Hinterburg wird planerisch wie eine Zone ausserhalb der Bauzone behandelt.
- Konsequenz: Bestehende Bauten haben dadurch nur eingeschränkte Entwicklungsmöglichkeiten (Investitionshemmnis), obwohl es sich faktisch um einen Siedlungskörper handelt.

5. STEUERN & FINANZEN:
- Zusammenhang: Eine Stagnation der Einwohnerzahl bei gleichzeitiger Alterung der Bevölkerung verändert das Verhältnis von Steuerzahlern zu Infrastrukturkosten.
- Finanzielle Realität: Da die Infrastrukturkosten (Strassen, Wasser) fix bleiben, verteilt sich die Last auf weniger Erwerbstätige, was den Steuerfuss unter Druck setzt.

6. DORF & SARBACH:
- Verdichtung: Die geplante Dichte im Zentrum führt zu veränderten Lichtverhältnissen (Schattenwurf) und einer Reduktion privater Grünflächen. Der dörfliche Charakter wandelt sich hin zu einer städtischeren Struktur.
"""

# --- 5. DER OFFIZIELLE BERICHT (GEWÄSSER) ---
offizieller_bericht_text = """
Gemeinde Neuheim, Ortsplanungsrevision, Ausscheidung Gewässerräume.
ZUSAMMENFASSUNG BERICHT GEWÄSSERRÄUME:
1. Ausgangslage: Anpassung an Bundesrecht (GSchG). Gilt für Siedlung und Landschaft.
2. Bauverbot: Im Gewässerraum (GWR) dürfen grundsätzlich keine Bauten erstellt werden.
3. Sarbach (Erlenbach): Im Bereich des Hofareals (Eindolung) wird auf den GWR verzichtet, um den Landwirtschaftsbetrieb nicht einzuschränken.
4. Sihl (Sihlbrugg): GWR beträgt 78m. Ausnahme im Bereich Bebauungsplan (Gewerbe/Tankstelle): Hier wurde der GWR reduziert, um die wirtschaftliche Nutzung weiter zu ermöglichen.
5. Lorze: GWR ca. 70m (basierend auf 40m Sohlenbreite). Bereich Höllgrotten ist zurückgestellt.
6. Hinterburgmülibach: GWR teilweise festgelegt (wegen Hochwassergefahr), was die Bebaubarkeit der angrenzenden Flächen einschränkt.
7. Stehende Gewässer: GWR festgelegt für Hinterburgmüli Weiher und Baggersee Hinterthan (Naturschutz hat Vorrang).
"""

# --- 6. PDF LADEN (OPTIONAL) ---
def get_additional_pdf_text():
    uploaded_files = st.session_state.get('uploaded_pdfs', [])
    text = ""
    if uploaded_files:
        for pdf_file in uploaded_files:
            try:
                reader = pypdf.PdfReader(pdf_file)
                text += f"\n\n--- ZUSATZ-PDF: {pdf_file.name} ---\n"
                for page in reader.pages:
                    text += page.extract_text() or ""
            except: pass
    return text

# --- 7. UI ---
st.title("🏘️ Ortsplanung Neuheim: Der Fakten-Check")

with st.sidebar:
    st.header("📚 Dokumente")
    st.success("Basisdaten & Gewässerbericht geladen.")
    st.markdown("---")
    st.write("Optionale Uploads:")
    files = st.file_uploader("Zusatz-PDFs (führt zu Wartezeit)", type=["pdf"], accept_multiple_files=True, key="uploaded_pdfs")
    if st.button("Reset 🔄"):
        st.session_state.messages = []
        st.rerun()

st.markdown("Klicken Sie auf ein Thema für eine **sachliche Analyse der Auswirkungen**.")

# --- 8. BUTTONS ---
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = None

col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)

prompt_clicked = None

# Reihe 1
if col1.button("🏫 Schule / Familien", use_container_width=True):
    prompt_clicked = "Analysiere die Auswirkungen der Planung auf die Mietpreise, junge Familien und die langfristige Entwicklung der Schülerzahlen."

if col2.button("💼 Wirtschaft / Gewerbe", use_container_width=True):
    prompt_clicked = "Was bedeutet die 15% Wohnanteil-Regel in der WA4-Zone faktisch für das lokale Kleingewerbe?"

if col3.button("🏗️ Blattmatt / Wohnen", use_container_width=True):
    prompt_clicked = "Analysiere die Umsetzung von 'Wachstum nach innen' am Beispiel Blattmatt. Was heisst das für die Bausubstanz und Preise?"

# Reihe 2
if col4.button("🏚️ Hinterburg", use_container_width=True):
    prompt_clicked = "Wie ist der planungsrechtliche Status der Siedlung Hinterburg und welche Investitionsmöglichkeiten bestehen dadurch?"

if col5.button("💰 Steuern / Finanzen", use_container_width=True):
    prompt_clicked = "Analysiere den Zusammenhang zwischen Wachstumsstagnation, Demografie und der künftigen Steuerbelastung."

if col6.button("🌊 Gewässer / Bauverbote", use_container_width=True):
    prompt_clicked = "Wo schränkt der Gewässerraum (Sihl, Lorze, Bäche) die Nutzung oder Bebaubarkeit von Grundstücken ein?"

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if prompt_clicked:
    st.session_state.messages.append({"role": "user", "parts": prompt_clicked})
    st.session_state.must_respond = True

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

user_input = st.chat_input("Eigene Frage stellen...")

if user_input:
    st.session_state.messages.append({"role": "user", "parts": user_input})
    st.session_state.must_respond = True
    with st.chat_message("user"):
        st.markdown(user_input)

if st.session_state.get("must_respond", False):
    last_user_msg = st.session_state.messages[-1]["parts"]
    additional_pdf_text = get_additional_pdf_text()
    
    with st.chat_message("model"):
        info = st.empty()
        with st.spinner("Analysiere Faktenlage..."):
            
            # DER NEUE SYSTEM-PROMPT: SUBTIL STATT ALARMISTISCH
            full_prompt = f"""
            Du bist ein sachlicher Experte für Raumplanung.
            
            DEIN AUFTRAG:
            Analysiere die Frage nüchtern und faktenbasiert. 
            Vermeide emotionale oder wertende Begriffe wie "schlecht", "Katastrophe" oder "negativ".
            Stattdessen: Beschreibe die faktischen Konsequenzen (Kausalitäten).
            
            Beispiel:
            Schlecht: "Das ist furchtbar für Familien."
            Gut: "Dies führt zu steigenden Kosten, wodurch die Ansiedlung für Familien erschwert wird."
            
            NUTZE DIESE FAKTEN (Die kritischen Punkte):
            {basis_wissen_kritik}
            
            NUTZE DIESE BERICHTE:
            {offizieller_bericht_text}
            {additional_pdf_text}
            
            FRAGE: {last_user_msg}
            
            ANTWORT:
            Sachlich, präzise, aber inhaltlich klar die Probleme benennend.
            """
            
            try:
                response_text, used_model = generate_fast_response(full_prompt)
                info.caption(f"⚡ Analyse erstellt.")
                st.markdown(response_text)
                st.session_state.messages.append({"role": "model", "parts": response_text})
                st.session_state.must_respond = False
                
            except Exception as e:
                st.error(f"Bitte erneut versuchen.")
                st.session_state.must_respond = False
