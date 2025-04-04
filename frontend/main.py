import streamlit as st
from pathlib import Path
import os
from dotenv import load_dotenv
import requests
from scipy.io.wavfile import write
import queue
import sounddevice as sd
import vosk
import json
from frontend.middleware import call_backend_test

load_dotenv()

HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/openai/whisper-small"

def transcribe_audio(file_path):
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
    with open(file_path, "rb") as f:
        audio_data = f.read()
    response = requests.post(HF_API_URL, headers=headers, data=audio_data, params={"language": "fr"})
    if response.status_code == 200:
        return response.json().get("text", "")
    else:
        return f"Erreur : {response.status_code} - {response.text}"

def record_audio_to_file(filename="output.wav", duration=5):
    fs = 16000
    st.info("🎙 Enregistrement en cours... Parlez maintenant")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="int16")
    sd.wait()
    write(filename, fs, audio)
    return filename

def main():
    # Create sidebar buttons
    st.sidebar.title("Navigation")
    selected_page = st.sidebar.radio("Go to", ["Default App", "README", "Game"])
    
    if selected_page == "Default App":
        st.header("Welcome to the Default ForgeAI Application")
        backend_response = call_backend_test()
        if backend_response:
            st.success(backend_response.get("message"))
            st.write("Data")
            data = backend_response.get("data")
            st.write(data)
        else:
            st.error('Backend is not responding')
            
    elif selected_page == "Game":
        game()
            
    else:  # README page
        st.header("Guidelines for Application Automation and Management")
        try:
            readme_path = Path(__file__).parent.parent / "README.md"
            with open(readme_path, "r", encoding="utf-8") as f:
                readme_content = f.read()
            st.markdown(readme_content)
        except FileNotFoundError:
            st.error("README.md file not found")

def game():
    st.title("Jeu de rôle : Médecin de catastrophe")
    st.subheader("🎭 Détails du jeu de rôle")
    st.markdown("""
        **Contexte** : Vous êtes un médecin en mission humanitaire dans une zone sinistrée.  
        **Objectif** : Interagir avec un agent conversationnel pour prendre des décisions médicales.  
        **Contraintes** : Matériel limité, priorisation des victimes, stress environnemental.
    """)

    st.subheader("📨 Communication")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        st.markdown(msg)

    st.subheader("💬 Envoyer une instruction")

    user_input = st.text_input("Votre message :", key="user_prompt")

    # 🎙 Whisper HuggingFace vocal
    if st.button("🎙 Parler avec Whisper"):
        filename = "output.wav"
        file_path = record_audio_to_file(filename, duration=6)  # 6s max pour Hugging Face free tier
        with st.spinner("⏳ Transcription en cours..."):
            text = transcribe_audio(file_path)
            st.session_state.transcribed_text = text
            st.success("Transcription terminée ✅")

    # Affiche le texte reconnu
    if "transcribed_text" in st.session_state:
        st.write("📝 Texte transcrit :", st.session_state.transcribed_text)
        # Facultatif : proposer de copier le texte dans le champ
        if st.button("🡇 Copier la transcription dans le champ"):
            st.session_state["user_prompt"] = st.session_state["transcribed_text"]

    if st.button("Envoyer"):
        msg = user_input.strip()
        if msg:
            st.session_state.chat_history.append(f"👤 Vous : {msg}")
            from frontend.middleware import call_backend_test
            backend_response = call_backend_test()
            response_text = backend_response.get("message", "Erreur")
            st.session_state.chat_history.append(f"🤖 Assistant : {response_text}")
        else:
            st.warning("Veuillez entrer un message avant d'envoyer.")