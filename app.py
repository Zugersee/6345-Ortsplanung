st.stop()

genai.configure(api_key=api_key)

# --- 3. FIXES WISSEN (Dein Bericht) ---
# Das ist der Text, den du oben geliefert hast. Er dient als "Insider-Wissen".
basis_wissen = """
KRITISCHER BERICHT ZUR LAGE (Quelle: Engagierter Einwohner):
- Allgemein: Wachstum soll laut Gemeinde nur nach innen möglich sein. Praxisbeispiel Blattmatt: Abriss intakter Bausubstanz.
- Wohnraum: Bezahlbarer Wohnraum entsteht nur auf der grünen Wiese, nicht durch Verdichtung.
- Parzelle 7 (Landolt/Säntisstrasse): War W2, soll in Landwirtschaftszone zurückgezont werden. Kritik: Sollte besser W3 für bezahlbaren Wohnraum werden (Ebene bis Hügelfuss Hirschleten).
- Industriegebiet (WA4): Name suggeriert Wohnen/Arbeiten. Aber: Wohnanteil auf 15% beschränkt. Das ist eigentümerfeindlich und verhindert Wohnraum.
- Bürgergemeinde: Sandgefüllter Keller an der Oberlandstrasse darf wohl 20 Jahre nicht genutzt werden.
- Technikmuseum ZDT: Zukunft in Landwirtschaftszone unsicher, Umzonung in OeIB wurde verpasst.
- Hinterburg: Kantonale Raumplanung findet Richtlinien für Bauen ausserhalb Bauzone hier unangemessen (da faktisch Siedlungscharakter). Gemeinde/Planer (R+K) haben Chance verpasst, ein Entwicklungskonzept (Kombistudie) zu erstellen.
"""

# --- 4. FUNKTIONEN ---
@st.cache_resource
def get_model():
    # Wir nutzen Flash für schnelle Verarbeitung grosser Textmengen
    return genai.GenerativeModel('gemini-1.5-flash') 

def extract_text_from_pdf(uploaded_file):
    try:
        pdf_reader = pypdf.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        return f"Fehler beim Lesen von {uploaded_file.name}: {e}"

# --- 5. SIDEBAR: DOKUMENTE LADEN ---
with st.sidebar:
    st.header("📂 Wissensbasis erweitern")
    st.markdown("Lade hier die offiziellen Dokumente hoch (Erläuterungsbericht, Zonenplan-Bericht, etc.), damit der Bot Details zu Steuern und Schule kennt.")
    
    uploaded_files = st.file_uploader("PDFs hochladen", type=["pdf"], accept_multiple_files=True)
    
    st.markdown("---")
    if st.button("Chat zurücksetzen 🗑️"):
        st.session_state.messages = []
        st.session_state.pdf_content = "" # Cache leeren
        st.rerun()

# --- 6. DATENVERARBEITUNG ---
if "pdf_content" not in st.session_state:
    st.session_state.pdf_content = ""

# Wenn neue Dateien hochgeladen wurden, Text extrahieren
if uploaded_files:
    raw_text = ""
    for pdf in uploaded_files:
        with st.spinner(f"Analysiere {pdf.name}..."):
            raw_text += f"\n--- INHALT AUS DATEI: {pdf.name} ---\n"
            raw_text += extract_text_from_pdf(pdf)
    
    # Nur aktualisieren, wenn sich was geändert hat, um Kosten zu sparen
    if len(raw_text) > len(st.session_state.pdf_content):
        st.session_state.pdf_content = raw_text
        st.success(f"{len(uploaded_files)} Dokumente erfolgreich integriert!")

# --- 7. SYSTEM PROMPT ---
# Hier definieren wir die Logik: Faktenbasiert, Konsequenzen aufzeigend.

system_instruction = f"""
Du bist ein sachlicher, analytischer Experte für Raumplanung und Gemeindeentwicklung, spezialisiert auf die Ortsplanungs-Revision der Gemeinde Neuheim.

DEINE AUFGABE:
Beantworte Fragen der Einwohner zu den Konsequenzen der Planung.
Analysiere die Auswirkungen auf: Finanzen, Steuern, bauliche Möglichkeiten, Schule, Verkehr und Eigentum.

DEINE WISSENSBASIS:
1. Ein kritischer Insider-Bericht (siehe unten).
2. Offizielle Dokumente, die der User hochgeladen hat (siehe unten).

VERHALTENSREGELN:
1. **Faktenbasiert:** Keine pädagogischen Floskeln. Keine Begrüssungs-Lyrik. Komm sofort zum Punkt.
2. **Konsequenzen nennen:** Wenn der User fragt "Was bedeutet das für mich?", erkläre die direkte Auswirkung (z.B. "Das bedeutet, Sie können auf Parzelle X nicht mehr bauen" oder "Das könnte zu Steuererhöhungen führen, weil...").
3. **Quellenbezug:** Wenn eine Info aus dem "kritischen Bericht" stammt, kennzeichne das subtil (z.B. "Kritiker merken an..." oder "In der Praxis zeigt sich..."). Wenn es aus den offiziellen PDFs kommt, nutze diese Fakten.
4. **Widersprüche aufzeigen:** Wenn der offizielle Bericht etwas verspricht (z.B. Wachstum), aber der Insider-Bericht das Gegenteil beweist (z.B. Blattmatt), stelle beide Sichtweisen gegenüber.

--- BEGINN BASISWISSEN (INSIDER BERICHT) ---
{basis_wissen}
--- ENDE BASISWISSEN ---

--- BEGINN ZUSATZWISSEN AUS DOKUMENTEN ---
{st.session_state.pdf_content}
--- ENDE ZUSATZWISSEN ---
"""

model = get_model()

# --- 8. CHAT INTERFACE ---

st.title("🏘️ Ortsplanung Neuheim: Der Fakten-Check")
st.markdown("""
Stellen Sie Fragen zur Revision. Was bedeutet sie konkret für:
* 💰 **Geldbeutel:** Steuern, Gebühren, Liegenschaftswert
* 🏗️ **Bauen:** Ausnützung, Aufzonung, Rückzonung
* 🏫 **Zukunft:** Schule, Verkehr, Dorfentwicklung
""")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

if prompt := st.chat_input("Ihre Frage zur Ortsplanung (z.B. Was passiert mit der W2 Zone?"):
    st.session_state.messages.append({"role": "user", "parts": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("model"):
        with st.spinner("Analysiere Dokumente und Konsequenzen..."):
            try:
                # Wir bauen den Chat jedes Mal neu auf mit dem aktuellen System Prompt (falls neue PDFs kamen)
                # Google Gemini API 'count_tokens' Workaround: Wir senden System Prompt + History
                
                # Konfiguration des Chats
                chat = model.start_chat(history=[])
                
                # Wir senden den System Prompt als erste Nachricht (Trick für Context) oder nutzen system_instruction parameter wenn unterstützt
                # Hier "injizieren" wir es in den aktuellen Prompt, da Streamlit State stateless ist
                final_prompt = system_instruction + "\n\nFRAGE DES USERS: " + prompt
                
                response = model.generate_content(final_prompt)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "model", "parts": response.text})
            except Exception as e:
                st.error(f"Fehler: {e}")
