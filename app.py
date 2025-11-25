import streamlit as st
import google.generativeai as genai
import pypdf
import os
import time

# --- 1. KONFIGURATION ---
st.set_page_config(
    page_title="Ortsplanung Neuheim: Der Check",
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

# --- 3. MODELL (TURBO) ---
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

# --- 4. BASIS-WISSEN (DER KRITISCHE KERN) ---
basis_wissen_kritik = """
FAKTEN FÜR DIE ANALYSE (KRITISCHE AUSWIRKUNGEN):

1. MIETER / JUNGE FAMILIEN:
- Fakt: Planung setzt auf "Ersatzneubau" (Abriss Altes -> Bau Neues).
- Konsequenz: Neubauten sind deutlich teurer. Günstiger Altbau verschwindet.
- Risiko: Verdrängung aus der Gemeinde, da unbezahlbar.

2. EIGENHEIMBESITZER (MITTELALTER & SENIOREN):
- Fakt: Stagnation der Einwohnerzahl bei gleichzeitiger Alterung ("Überalterung").
- Konsequenz: Weniger Steuerzahler müssen die fixen Infrastrukturkosten (Strassen, Wasser, Schule) tragen.
- Risiko: Langfristig steigender Steuerfuss und Wertverlust bei Immobilien, wenn das Dorf an Attraktivität verliert (Läden schliessen).

3. LEHRER / SCHULE:
- Fakt: Fehlender Zuzug junger Familien wegen hoher Mietpreise.
- Konsequenz: Sinkende Schülerzahlen.
- Risiko: Stellenabbau, Klassenzusammenlegungen, Schulstandort verliert Qualität.

4. GEWERBE:
- Fakt: WA4-Zone erlaubt nur 15% Wohnen.
- Risiko: Kleingewerbe (Handwerker), das Wohnen & Arbeiten verbindet, findet keinen Platz.

5. SPEZIFISCHE ORTE:
- Blattmatt: Abriss statt Verdichtung.
- Hinterburg: Investitionsstau (falsche Zonenzuweisung).
- Parzelle 7: Rückzonung vernichtet Baupotential.
"""

# --- 5. BERICHT GEWÄSSER ---
offizieller_bericht_text = """
ZUSAMMENFASSUNG GEWÄSSERRÄUME:
- Bauverbot in Gewässerräumen (Sihl, Lorze, Bäche).
- Sihl (Sihlbrugg): 78m Raum, reduziert bei Gewerbezonen.
- Sarbach: Verzicht auf Raum bei Hof Erlenbach (Eindolung).
- Hinterburgmülibach: Teilweise Bauverbote wegen Hochwassergefahr.
"""

# --- 6. PDF LADEN ---
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
st.title("🏘️ Ortsplanung Neuheim: Der Check")

with st.sidebar:
    st.header("⚙️ Menü")
    st.success("Daten geladen.")
    if st.button("Neuer Chat 🔄"):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.file_uploader("Zusatz-PDFs (optional)", type=["pdf"], accept_multiple_files=True, key="uploaded_pdfs")

st.markdown("Klicken Sie auf Ihre Lebenssituation für eine **kurze Analyse**.")

# --- 8. BUTTONS (USER ROLES) ---
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = None

c1, c2, c3, c4 = st.columns(4)

prompt_clicked = None

if c1.button("👨‍👩‍👧 Junge Familie / Mieter", use_container_width=True):
    prompt_clicked = "Ich bin eine junge Familie in einer Mietwohnung. Was sind meine Vor- und Nachteile bei Annahme oder Ablehnung?"

if c2.button("🏡 Eigenheim (Mittelalter)", use_container_width=True):
    prompt_clicked = "Ich bin im mittleren Alter und habe ein Eigenheim. Was bedeutet die Planung für Steuern und Wert?"

if c3.button("👴 Eigenheim (Senioren)", use_container_width=True):
    prompt_clicked = "Ich bin Senior im Eigenheim. Was sind die Risiken für mich (Steuern, Versorgung, Dorfleben)?"

if c4.button("im öffentlichen Dienst / Schule", use_container_width=True):
    prompt_clicked = "Ich bin Lehrer / arbeite an der Schule. Was heisst die Planung für meinen Job?"

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if prompt_clicked:
    st.session_state.messages.append({"role": "user", "parts": prompt_clicked})
    st.session_state.must_respond = True

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

user_input = st.chat_input("Eigene Frage (z.B. 'Was passiert mit der Hinterburg?')...")

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
        with st.spinner("Erstelle Vergleich..."):
            
            # DER NEUE PROMPT FÜR STRUKTURIERTE ANTWORTEN
            full_prompt = f"""
            Du bist ein sachlicher Planungs-Analyst.
            
            DEIN AUFTRAG:
            Antworte auf die Frage des Bürgers kurz, klar und strukturiert.
            Nutze ZWINGEND das untenstehende Format für die Antwort.
            Keine langen Texte. Nutze Bulletpoints.
            
            DAS FORMAT:
            
            **Analyse für Ihre Situation:**
            
            **🔴 BEI ANNAHME DER VORLAGE (Status Quo):**
            * **Ihr Risiko:** [Das grösste Risiko aus dem Basiswissen, z.B. Mieterhöhung/Steuererhöhung]
            * **Vermeintlicher Vorteil:** Planung ist abgeschlossen (Rechtssicherheit), aber auf tiefem Niveau.
            
            **🟢 BEI ABLEHNUNG (NEIN-Stimme):**
            * **Ihr Gewinn:** [Die Chance auf Besserung, z.B. bezahlbarer Wohnraum durch Neuplanung]
            * **Nachteil:** Zeitverzögerung (es braucht eine neue Runde), dafür steigt die Qualität.
            
            **Fazit:** [Ein kurzer Satz, der logisch herleitet, warum Ablehnung für diese Person rational besser ist].
            
            NUTZE DIESES WISSEN FÜR DIE FAKTEN:
            {basis_wissen_kritik}
            {offizieller_bericht_text}
            {additional_pdf_text}
            
            FRAGE: {last_user_msg}
            """
            
            try:
                response_text, used_model = generate_fast_response(full_prompt)
                info.caption(f"⚡ Analyse fertig.")
                st.markdown(response_text)
                st.session_state.messages.append({"role": "model", "parts": response_text})
                st.session_state.must_respond = False
                
            except Exception as e:
                st.error(f"Bitte noch einmal klicken.")
                st.session_state.must_respond = False
