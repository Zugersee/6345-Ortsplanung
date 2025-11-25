import streamlit as st
import google.generativeai as genai
import os
import time
import pypdf  # WICHTIG: Dieser Import fehlte in deinem ursprünglichen Code!

# --- 1. KONFIGURATION ---
st.set_page_config(
    page_title="Ortsplanung Neuheim: Der Fakten-Check",
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
        'gemini-2.0-flash-lite',
        'gemini-1.5-flash' # Fallback hinzugefügt
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

# --- 4. WISSENSDATENBANK ---
vorteile_planung = """
1. RECHTSSICHERHEIT: Die Planung ist abgeschlossen und schafft sofortige Rechtssicherheit für Baugesuche.
2. GEWÄSSERSCHUTZ: Die Vorlage setzt übergeordnetes Recht um (Art. 36a GSchG) und fördert die Ökologie.
3. BAUGRENZEN: Es werden klare Grenzen für das Wachstum nach innen gesetzt.
"""
basis_wissen_kritik = """
POINTIERTE KRITISCHE FAKTEN:

1. MIETER & FAMILIEN:
- Fakt: Planung setzt auf "Ersatzneubau" (z.B. Blattmatt). Konsequenz: Massive Mietpreisanstiege, Verdrängungseffekt.

2. FINANZEN & STEUERN:
- Fakt: Durch fehlendes Wachstum stagniert die Einwohnerzahl und altert. Konsequenz: Last der Infrastrukturkosten verteilt sich auf weniger Erwerbstätige. Drohende Steuererhöhung.

3. SCHULE & LEHRER:
- Fakt: Hohe Mieten verhindern Zuzug junger Familien. Konsequenz: Schülerzahlen sinken, Klassenzusammenlegungen und Gefährdung des Schulstandortes.

4. EIGENTUM & HINTERBURG:
- Fakt: Siedlung Hinterburg wird planerisch als "ausserhalb Bauzone" behandelt. Konsequenz: Planerischer Stillstand, Investitionshemmnis, eingeschränkte An-/Umbau-Möglichkeiten.

5. GEWERBE:
- Fakt: WA4-Zone deckelt Wohnanteil auf 15%. Konsequenz: Hemmt modernes Kleingewerbe (Wohnen/Arbeiten).

6. DORFCHARAKTER:
- Fakt: Verdichtung im Zentrum führt zu Schattenwurf und Verlust privater Grünflächen. Konsequenz: Wandel des dörflichen Charakters.
"""

# --- 5. DATEN LADEN ---
def get_additional_pdf_text():
    uploaded_files = st.session_state.get('uploaded_pdfs', [])
    text = ""
    if uploaded_files:
        for pdf_file in uploaded_files:
            try:
                reader = pypdf.PdfReader(pdf_file)
                text += f"\n\n--- ZUSATZ-PDF: {pdf_file.name} ---\n"
                for page in reader.pages: 
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted
            except Exception as e:
                st.error(f"Fehler beim Lesen von {pdf_file.name}: {e}")
    return text

@st.cache_resource
def load_data():
    text = ""
    current_dir = os.getcwd()
    # Sicherstellen, dass wir nur txt files lesen
    try:
        txt_files = [f for f in os.listdir(current_dir) if f.lower().endswith(('.txt'))]
        for f in txt_files:
            try:
                with open(f, "r", encoding="utf-8") as file:
                    content = file.read()
                    text += f"\n\n--- DOKUMENT: {f} ---\n{content}"
            except: pass
    except: pass # Falls os.listdir fehlschlägt
    return text

files_text = load_data() 

# --- 6. UI & BUTTONS ---
st.title("🏘️ Ortsplanung Neuheim: Der Fakten-Check")
st.markdown("Klicken Sie auf Ihre Lebenssituation für eine **detaillierte Analyse**.")

with st.sidebar:
    st.header("⚙️ Menü")
    st.success("Basisdaten & Argumentarium geladen.")
    if st.button("Reset 🔄"):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.file_uploader("Zusatz-PDFs (optional)", type=["pdf"], accept_multiple_files=True, key="uploaded_pdfs")

button_prompts = {
    "👨‍👩‍👧 Familie & Mieter": "Ich bin Mieter / junge Familie. Was sind die Vor- und Nachteile der Planung für mich?",
    "🏡 Eigenheim (Steuern)": "Ich bin Eigenheimbesitzer. Was bedeutet die Planung für meine Steuern und die Bebaubarkeit meines Grundstücks?",
    "🏫 Schule & Lehrer": "Ich arbeite an der Schule. Was bedeutet die Demografie-Entwicklung für meinen Arbeitsplatz?",
    "💰 Steuerzahler (Finanzen)": "Warum droht bei Annahme der Vorlage eine Steuererhöhung? Erkläre den Zusammenhang mit der Stagnation.",
    "🛠️ Gewerbe (WA4-Zone)": "Was bedeutet die 15% Wohnanteil-Regel in der WA4-Zone faktisch für das lokale Gewerbe und Wohnen/Arbeiten?",
    "🛒 Dorfladen / Wirtschaft": "Welche Folgen hat die Planung für Dorfläden und die Nahversorgung im Zentrum?",
    "🏗️ Blattmatt (Wohnen)": "Was passiert konkret in der Blattmatt? Analyse zu 'Ersatzneubau' vs. günstigem Wohnraum.",
    "🏘️ Dorfkern & Charakter": "Wie verändert sich der Charakter im Dorfkern/Sarbach? (Schatten, Grünflächen, Dichte).",
    "🏚️ Siedlung Hinterburg": "Welche klaren Nachteile entstehen für Eigentümer der Siedlung Hinterburg durch die Zonierung?"
}

clicked_button_name = None

# 3x3 Grid
st.markdown("### 🎯 Interessensgruppen")
cols = st.columns(3)

for i, (name, prompt) in enumerate(button_prompts.items()):
    col = cols[i % 3]
    if col.button(name, use_container_width=True, key=f"btn_{i}"):
        clicked_button_name = name

# --- 7. CHAT LOGIK ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Wenn Button geklickt, Prompt setzen
if clicked_button_name:
    prompt_to_send = button_prompts[clicked_button_name]
    st.session_state.messages.append({"role": "user", "parts": prompt_to_send})
    st.session_state.must_respond = True

# Chatverlauf anzeigen
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# Manuelle Eingabe
user_input = st.chat_input("Oder stellen Sie eine eigene, spezifische Frage...")
if user_input:
    st.session_state.messages.append({"role": "user", "parts": user_input})
    st.session_state.must_respond = True
    st.rerun()

# --- 8. KI ANTWORT (OPTIMIERT) ---

if st.session_state.get("must_respond", False) and st.session_state.messages:
    last_user_msg = st.session_state.messages[-1]["parts"]
    additional_pdf_text = get_additional_pdf_text()
    
    with st.chat_message("model"):
        info = st.empty()
        with st.spinner("Analysiere Faktenlage und Zusammenhänge..."):
            
            # --- NEUER PROMPT FÜR MEHR TIEFE ---
            full_prompt = f"""
            Du bist ein erfahrener, kritischer Raumplanungs-Experte für die Gemeinde Neuheim.
            Deine Aufgabe ist es, dem Bürger nicht nur Schlagworte zu liefern, sondern die Zusammenhänge verständlich zu erklären.

            AUFTRAG:
            Antworte differenziert, aber glasklar. Vermeide reine Stichworte. Schreibe in ganzen, prägnanten Sätzen.
            Erkläre bei negativen Folgen das "Warum" (Ursache -> Wirkung).

            NUTZE FOLGENDE STRUKTUR FÜR DIE ANTWORT:

            ### 🧐 Die Situation
            Ein bis zwei Sätze zur Einordnung der Frage in den aktuellen Planungskontext.

            ### ✅ Szenario A: Bei ANNAHME der Vorlage (JA)
            * **Der planerische Gewinn:** Erkläre kurz den formalen Vorteil (z.B. Rechtssicherheit, Gewässerschutz) basierend auf den Fakten.
            * **Die konkrete Auswirkung (Kritik):** Analysiere das Risiko im Detail. Erkläre den Mechanismus: Warum passiert das? (z.B. Weshalb führt die Planung zu höheren Mieten oder Steuererhöhungen? Verweise auf Ersatzneubau, Stagnation etc.). Sei hier sehr deutlich.

            ### ✨ Szenario B: Bei ABLEHNUNG (NEIN)
            * **Die Chance:** Was könnte bei einer Neuplanung besser gemacht werden (z.B. aktive Bodenpolitik, preisgünstiger Wohnraum, Erhalt Dorfcharakter)?
            * **Der Preis:** Die Zeitverzögerung bis zur neuen Vorlage.

            ### ⚖️ Klartext-Fazit
            Ein zusammenfassender Satz, der den Kernkonflikt für die betroffene Personengruppe auf den Punkt bringt.

            DATENBASIS:
            {basis_wissen_kritik}
            {vorteile_planung} 
            
            DOKUMENTE & KONTEXT: {files_text}
            ZUSATZ-INFOS: {additional_pdf_text}
            
            FRAGE DES BÜRGERS: {last_user_msg}
            """
            
            try:
                response_text, used_model = generate_fast_response(full_prompt)
                info.caption(f"⚡ Analyse erstellt mit {used_model}")
                
                st.markdown(response_text)
                st.session_state.messages.append({"role": "model", "parts": response_text})
                st.session_state.must_respond = False
                
            except Exception as e:
                st.error(f"Fehler bei der Analyse. Ursache: {e}. Bitte kurz warten und erneut versuchen.")
                st.session_state.messages.append({"role": "model", "parts": "Entschuldigung, die Analyse konnte aufgrund eines technischen Problems nicht abgeschlossen werden."})
                st.session_state.must_respond = False
