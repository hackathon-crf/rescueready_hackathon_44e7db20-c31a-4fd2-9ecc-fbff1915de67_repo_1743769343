import streamlit as st
import time
from pathlib import Path
import os
from dotenv import load_dotenv
import requests
from scipy.io.wavfile import write
import queue
import sounddevice as sd
import json
import numpy as np
import threading
from transformers import pipeline
from frontend.middleware import call_backend_test

load_dotenv()

# recording_flag = {"active": False}

HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/openai/whisper-small"
BACKEND_URL = "http://localhost:8090/api/app/transcribe/"

def tts_huggingface(text: str, filename="tts_output.wav"):
    retries = 3
    # url = "https://api-inference.huggingface.co/models/plgnk/tts-french-model"
    url = "https://api-inference.huggingface.co/models/facebook/fastspeech2-en-ljspeech"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
    txt2 = "je suis un test"
    for attempt in range(retries):
        response = requests.post(url, headers=headers, json={"inputs": txt2})
        
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            return filename
        elif response.status_code == 503:
            print(f"[Tentative {attempt+1}/{retries}] Serveur indisponible. Nouvelle tentative dans 5s...")
            time.sleep(5)
        else:
            print(f"Erreur Hugging Face TTS : {response.status_code} - {response.text}")
            break
    
    return None

def transcribe_audio(file_path):
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
    with open(file_path, "rb") as f:
        audio_data = f.read()
    response = requests.post(HF_API_URL, headers=headers, data=audio_data, params={"language": "fr"})
    if response.status_code == 200:
        return response.json().get("text", "")
    else:
        return f"Erreur : {response.status_code} - {response.text}"

def send_to_backend(file_path):
    with open(file_path, "rb") as f:
        files = {"file": (file_path, f, "audio/wav")}
        response = requests.post(BACKEND_URL, files=files)
    if response.status_code == 200:
        return response.json().get("text", "nothing to return")
    else:
        return f"Erreur: {response.status_code} - {response.text}"

def record_audio(filename="output.wav", duration=6, recording_flag=None):
    fs = 16000
    buffer = []

    def callback(indata, frames, time, status):
        if not recording_flag["active"]:
            raise sd.CallbackStop()
        buffer.append(indata.copy())

    try:
        with sd.InputStream(samplerate=fs, channels=1, dtype='int16', callback=callback):
            while recording_flag["active"]:
                sd.sleep(100)
    except sd.CallbackStop:
        pass

    audio = np.concatenate(buffer)
    write(filename, fs, audio)
    print("Enregistrement terminé.")
    text = send_to_backend(filename)
    # On ne peut pas modifier session_state ici, donc on utilisera un autre mécanisme pour le montrer dans l’UI
    # Astuce : sauvegarder le texte dans un fichier temporaire ou une variable globale
    with open("last_transcription.txt", "w") as f:
        f.write(text)