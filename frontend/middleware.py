import requests
from settings.config import settings
from dotenv import load_dotenv
import os
import streamlit as st
import json


# Load environment variables from .client_env
load_dotenv(".client_env")

# Get environment variables, with fallbacks
DOMAIN_NAME = os.getenv("DOMAIN_NAME", "localhost")
ROOT_PATH = os.getenv("ROOT_PATH", "")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8090")
RAG_API_ENDPOINT=os.getenv("RAG_API_ENDPOINT", "")
MISTRAL_API_KEY=os.getenv("ANTHROPIC_API_KEY", "")

def call_backend_test():
    try:
        # Construct URL with proper protocol and format
        # url = f"https://{DOMAIN_NAME}{ROOT_PATH}/api/app/test/"
        url = "http://localhost:8000/api/app/test/"
        print(f"Calling backend URL: {url}")

        params = {}
        response = requests.get(url, params=params)
        print(f"Response status: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"Error calling backend: {str(e)}")
        return {"error": str(e)}

