import streamlit as st
import google.generativeai as genai

# API Key Setup
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.text_input("API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    
    st.title("Welche Modelle habe ich?")
    
    try:
        st.write("Frage Google nach verfügbaren Modellen...")
        # Listet alle Modelle auf
        for m in genai.list_models():
            # Zeige nur die, die Text generieren können
            if 'generateContent' in m.supported_generation_methods:
                st.code(m.name) # Das ist der exakte Name, den wir brauchen
    except Exception as e:
        st.error(f"Fehler: {e}")
