import streamlit as st
import google.generativeai as genai
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

# --- 4. DAS BASIS-WISSEN (POINTIERT & KRITISCH) ---
# Dient als kritische Wissensbasis für den KI-Experten.
basis_wissen_kritik = """
POINTIERTE ANALYSE DER AUSWIRKUNGEN (FAKTENLAGE):

1. JUNGE FAMILIE / MIETER:
- Risiko (Mieten): Ersatzneubauten (z.B. Blattmatt) führen marktüblich zu stark höheren Mieten. Folge: Verdrängungseffekt, Zuzug junger Familien wird stark erschwert.
- Risiko (Umwelt): Verdichtung im Zentrum reduziert Grünflächen und Licht.
- Risiko (Steuern): Stagnation + Alterung = Risiko von Steuererhöhungen, die Mieter über Nebenkosten treffen.

2. EIGENHEIMBESITZER (ALLGEMEIN):
- Risiko (Steuern): Steuerdruck steigt, da Infrastrukturkosten auf weniger Erwerbstätige verteilt werden.
- Risiko (Hinterburg): Die Siedlung Hinterburg wird planungsrechtlich wie "Zone ausserhalb Bauzone" behandelt. Dies bedeutet **planerischen Stillstand, Investitionshemmnis** und stark **eingeschränkte** An-/Umbau-Möglichkeiten.
- Risiko (Gewässer): Bauverbote/Einschränkungen an Bächen und Weihern reduzieren die Nutzung des eigenen Landes.
- Vorteil (Evtl.): Potenzielle Wertsteigerung in Zonen mit massiver Verdichtung (Blattmatt) durch Preisanstieg.

3. SCHULE / LEHRER:
- Risiko (Arbeitsplatz): Fehlender Zuzug junger Familien (wegen hoher Mieten) führt zu sinkenden Schülerzahlen. Konsequenz: Klassenzusammenlegungen, potenzieller Stellenabbau, unsichere Planung.

4. WIRTSCHAFT / GEWERBE:
- Risiko: WA4-Zone deckelt Wohnanteil auf 15%. Das verhindert Kleingewerbe (Handwerker), das Wohnen & Arbeiten kombinieren will.

5. DORFLADEN / VERSORGUNG:
- Risiko: Stagnierende Einwohnerzahlen und fehlende junge Familien reduzieren die Kaufkraft. Das "Lädelisterben" wird begünstigt.
"""

# --- 5. ZUSATZDATEN LADEN (FÜR PDFs/TXTs) ---
def load_txt_data():
    text = ""
    current_dir = os.getcwd()
    # Simuliert das Laden von TXT-Dateien. PDF-Logik müsste hier integriert werden, wird aber vereinfacht dargestellt.
    txt_files = [f for f in os.listdir(current_dir) if f.lower().endswith(('.txt', '.pdf'))]
    for f in txt_files:
        try:
            with open(f, "r", encoding="utf-8") as file:
                text += f"\n\n--- ZUSATZ-DOKUMENT: {f} ---\n{file.read()}"
        except: pass
    return text

files_text = load_txt_data()

# --- 6. UI LAYOUT ---
st.title("🏘️ Ortsplanung Neuheim: Der Check")
st.markdown("Wählen Sie Ihren Fokus für eine **klare Chancen/Risiken-Analyse**.")

# --- 7. DIE 9-FELDER MATRIX (BUTTONS) ---
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = None

st.markdown("""
<style>
div.stButton > button:first-child {
    height: 3em;
    width: 100%;
}
</style>""", unsafe_allow_html=True)

# REIHE 1: PERSONEN
c1, c2, c3 = st.columns(3)
if c1.button("👨‍👩‍👧 Familie & Mieter"):
    st.session_state.last_prompt = "Ich bin Mieter / junge Familie. Was sind die konkreten Nachteile (Miete, Umfeld) bei Annahme?"
if c2.button("🏡 Eigenheim (Mittelalter/Senior)"):
    st.session_state.last_prompt = "Ich bin Eigenheimbesitzer. Was bedeutet die Planung für meine Steuern und die Bebaubarkeit meines Grundstücks?"
if c3.button("🏫 Schule & Lehrer"):
    st.session_state.last_prompt = "Ich arbeite an der Schule. Was bedeutet die Demografie-Entwicklung für meinen Arbeitsplatz?"

# REIHE 2: WIRTSCHAFT & GELD
c4, c5, c6 = st.columns(3)
if c4.button("💰 Steuerzahler"):
    st.session_state.last_prompt = "Warum droht bei Annahme der Vorlage eine Steuererhöhung? Erkläre den Zusammenhang mit der Stagnation."
if c5.button("🛠️ Gewerbe & Wirtschaft"):
    st.session_state.last_prompt = "Was bedeutet die WA4-Zone (15% Wohnanteil) für das lokale Gewerbe und Wohnen/Arbeiten?"
if c6.button("🛒 Dorfladen & Versorgung"):
    st.session_state.last_prompt = "Welche Folgen hat die Planung für Dorfläden und die Nahversorgung im Zentrum?"

# REIHE 3: ORTE & QUARTIERE
c7, c8, c9 = st.columns(3)
if c7.button("🏗️ Blattmatt (Wohnen)"):
    st.session_state.last_prompt = "Was passiert konkret in der Blattmatt? Analyse zu 'Ersatzneubau' vs. günstigem Wohnraum."
if c8.button("🏘️ Dorfkern & Sarbach"):
    st.session_state.last_prompt = "Wie verändert sich der Charakter im Dorfkern/Sarbach? (Schatten, Grünflächen, Dichte)."
if c9.button("🏚️ Siedlung Hinterburg"):
    st.session_state.last_prompt = "Welche klaren Nachteile entstehen für Eigentümer der Siedlung Hinterburg durch die Zonierung?" # Der Button-Text wurde geschärft

# --- 8. CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Wenn Button gedrückt wurde -> zur History hinzufügen
if st.session_state.last_prompt and (not st.session_state.messages or st.session_state.messages[-1]["parts"] != st.session_state.last_prompt):
    st.session_state.messages.append({"role": "user", "parts": st.session_state.last_prompt})
    st.session_state.must_respond = True
    st.session_state.last_prompt = None # Reset, damit es nicht doppelt feuert

# Chat rendern
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# --- 9. MANUELLER INPUT ---
st.markdown("---")
user_input = st.chat_input("Oder stellen Sie eine eigene, spezifische Frage (z.B. 'Was bedeutet es für die Hinterburg?')...")

if user_input:
    st.session_state.messages.append({"role": "user", "parts": user_input})
    st.session_state.must_respond = True
    st.rerun()

# --- 10. KI ANTWORT (EINHEITLICHE KRITISCHE ANALYSE) ---
if st.session_state.get("must_respond", False) and st.session_state.messages:
    last_msg = st.session_state.messages[-1]["parts"]
    
    with st.chat_message("model"):
        with st.spinner("Analysiere Faktenlage..."):
            
            full_prompt = f"""
            Du bist ein scharfer, sachlicher Planungs-Analyst.
            
            AUFTRAG:
            Antworte kurz, pointiert und ehrlich auf die Frage.
            Nutze ZWINGEND folgende, leicht verständliche Struktur für die Antwort.
            Beziehe dich IMMER auf die **Faktenlage** aus dem Basis-Wissen.
            
            DAS ERFORDERLICHE ANTWORT-FORMAT:
            
            ### 🔴 RISIKO BEI ANNAHME DER VORLAGE (Status Quo)
            * **Haupt-Nachteil 1**: [Der härteste, pointierte Fakt]
            * **Haupt-Nachteil 2**: [Der zweitwichtigste Fakt oder die Konsequenz aus 1]
            * **Fazit:** Ein Satz zur negativen Konsequenz.
            
            ### 🟢 CHANCE BEI ABLEHNUNG (Nein-Stimme)
            * **Der Gewinn:** [Die Chance auf Besserung oder eine bessere Planung, z.B. Beibehaltung von günstigem Wohnraum].
            
            NUTZE DIESE FAKTEN:
            {basis_wissen_kritik}
            {files_text}
            
            FRAGE: {last_msg}
            """
            
            try:
                response_text, _ = generate_fast_response(full_prompt)
                st.markdown(response_text)
                st.session_state.messages.append({"role": "model", "parts": response_text})
                st.session_state.must_respond = False
                
            except Exception as e:
                st.error("Ein technischer Fehler ist aufgetreten (Serverfehler). Bitte gleich nochmal versuchen.")
                st.session_state.must_respond = False
