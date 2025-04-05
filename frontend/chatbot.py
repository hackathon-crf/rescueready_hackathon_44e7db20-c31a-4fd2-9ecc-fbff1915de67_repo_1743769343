import streamlit as st
import requests
import json
from frontend.RAG import get_embeddings, get_collections, query_llm_with_embeddings


def display_chatbot():
    st.title("Simulation Médicale")

    # Liste déroulante avec les catégories
    categories = {
        "A": "Protection et sécurité",
        "B": "Urgences vitales",
        "C": "Affections médicales",
        "D": "Affections traumatiques",
        "E": "Affections circonstancielles",
        "F": "Souffrance psychique et comportements inhabituels",
        "H": "Situations particulières"
    }
    category = st.selectbox("Choisissez une catégorie", list(categories.values()))

    if st.button("Démarrer la simulation"):
        st.session_state["simulation_started"] = True
        st.session_state["conversation"] = ["Chatbot : Bonjour ! Comment puis-je vous aider ?"]

    if st.session_state.get("simulation_started", False):
        conversation = st.session_state.get("conversation", [])
        for msg in conversation:
            st.write(msg)

        user_input = st.text_input("Tapez un message...")
        if st.button("Envoyer"):
            response = requests.post("http://127.0.0.1:5000/chat", json={"message": user_input})
            if response.status_code == 200:
                st.write("Réponse du chatbot :", response.json()["response"])

        st.subheader("Enregistrement vocal")
        if st.button("Enregistrer un message vocal"):
            st.write("Enregistrement en cours... (Non implémenté)")
    
    collection_name = "PSE_fichesdecas"
    query = f"propose moi une simulation guidée formative sur {category}"
    embeddings = get_embeddings(query, collection_name)