# --- 10. KI ANTWORT ---

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
                # Wir nutzen hier direkt das Modell
                response_text, used_model = generate_fast_response(full_prompt)
                
                # Info-Anzeige (optional, welches Modell genutzt wurde)
                info.caption(f"⚡ Analyse erstellt mit {used_model}")
                
                st.markdown(response_text)
                st.session_state.messages.append({"role": "model", "parts": response_text})
                st.session_state.must_respond = False
                
            except Exception as e:
                st.error(f"Fehler bei der Analyse. Ursache: {e}. Bitte kurz warten und erneut versuchen.")
                st.session_state.messages.append({"role": "model", "parts": "Entschuldigung, die Analyse konnte aufgrund eines technischen Problems nicht abgeschlossen werden."})
                st.session_state.must_respond = False
