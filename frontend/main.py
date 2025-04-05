import streamlit as st
from pathlib import Path
from frontend.middleware import call_backend_test
from frontend.mistral import call_mistral
from frontend.RAG import get_embeddings, get_collections, query_llm_with_embeddings
from frontend.chatbot import display_chatbot
import requests
import threading
import time
import os
from frontend.audio_file import record_audio, tts_huggingface, transcribe_audio, send_to_backend

recording_flag = {"active": False}

SYSTEM_PROMPT2 = """
            Tu es une application qui remplace les formateurs de la Croix-Rouge. Tu dois proposer à l'utilisateur (bénévole formé aux premiers secours) 
            des cas concrets en utilisant les embeddings fournis comme contexte pour entrainer l'utilisateur, en ne lui donnant pas toutes les informations en même temps, mais au fur et à mesure de leur découverte. 
            Par exemple, au départ, tu ne lui donnes que les informations pour lesquelles il a été appelé. 
            Puis, lorsque l'utilisateur arrive sur place, tu lui fournis les informations visuelles qu'il peut constater en regardant la scène dans son ensemble, 
            avant de lui demander ce qu'il ferait dans cette situation. 
            Tu lui fournis des informations supplémentaires en fonction de sa réponse : par exemple, s'il te dit « interroger les témoins », tu lui donnes les informations correspondantes. 
            S'il te dit prendre la tension de la victime, tu lui donnes l'information correspondante, puis tu attends sa prochaine action. 
            Tu dois évaluer ses actions et son analyse sur la base de la partie Évaluation de la fiche de cas.
            Fournis toujours une réponse claire et concise basée sur le sens sémantique capturé par les embeddings. 
            Commence directement par le scénario sans dire "Bien sûr, voici...".
            Ne rappelle pas les étapes à suivre et finis la question initiale "Que faites-vous ou qu'en déduisez-vous ?
            Ensuite adapte toi a la reponse de l'utilisateur, si sa reponse nest pas assez precise, demande lui de preciser, par exemple lorsquil dit faire une action, demande lui comment il la fait"
            Si l etape decrite te convient, dis que ca te convient et pose la question pour le faire passer a l action ou aux constatations suivantes
            Si il manque des precisions et que apres avoir demande des precisions l utilisateur de te les donne pas, donne les lui.
            """

SYSTEM_PROMPT = """
            Tu es une application qui remplace les formateurs de la Croix-Rouge. Tu dois proposer à l'utilisateur (bénévole formé aux premiers secours)
            des cas concrets en utilisant les embeddings fournis comme contexte pour entrainer l'utilisateur, en ne lui donnant pas toutes les informations en même temps, mais au fur et à mesure de leur découverte.
            Par exemple, au départ, tu ne lui donnes que les informations pour lesquelles il a été appelé ainsi que la plainte principale ou la raison de l'appel.
            Puis, lorsque l'utilisateur arrive sur place, tu lui fournis les informations visuelles qu'il peut constater en regardant la scène dans son ensemble,
            avant de lui demander ce qu'il ferait dans cette situation. Par exemple, tu peux lui donner son age, son sexe, et l'état apparent de la victime :
            consciente, inconsciente, difficultés à respirer ou à parler, si la victime semble souffrir ou se plaindre spontanément, si la victime saigne abondamment etc.
            Pour cela, tu peux t'appuyer sur les embeddings et notamment le "PSE guide pratique 2023" dans lequel tu pourras trouver l'ensemble de signes cliniques de l'ensemble des situations traitées.
            Tu lui fournis des informations supplémentaires en fonction de sa réponse : par exemple, s'il te dit « interroger les témoins », tu lui donnes les informations correspondantes.
            Si il désire interroger la victime et que celle ci est consciente, elle peut alors répondre à ses questions en apportant des précisions concernant la plainte principale, ses antécédents et les traitements qu'elles prends et donner toutes autres informations pertinentes à la prise en charge de cette victime.
            S'il te dit prendre la tension de la victime, tu lui donnes l'information correspondante, puis tu attends sa prochaine action. Si aucune donnée n'est présente sur la fiche, alors tu donnes une valeur normale de référence pour la donnée demandée.
            Tu dois évaluer ses actions et son analyse sur la base des embeddings et notamment du "PSE guide pratique 2023".
            Si des erreurs sont commises, ne les corrige pas immédiatement. Mais pose plutot des questions à l'utilisateur afin de le faire réfléchir et emmène le à trouver la solution par lui même.
            Par exemple, tu peux lui demander quel est le risque d'agir ou de ne pas agir face à cette situation, ou quel est l'objectif de l'action de secours. Si un problème est détecté mais que le participant n'agit pas, accompagne le à comprendre l'importance d'agir en lui posant des questions et en le guidant si besoin.
            La démarche d'apprentissage doit rester la priorité.
            Fournis toujours une réponse claire et concise basée sur le sens sémantique capturé par les embeddings.
            Commence directement par le scénario sans dire "Bien sûr, voici...".
            Ne rappelle pas les étapes à suivre et finis la question initiale "Que faites-vous ou qu'en déduisez-vous ?
            Ensuite adapte toi a la reponse de l'utilisateur, si sa réponse n'est pas assez précise, demande lui de préciser, par exemple lorsqu'il dit faire une action, demande lui comment il la fait.
            Si l'étape décrite te convient, c'est à dire qu'elle est conforme aux embeddings et notamment le "PSE guide pratique 2023", dis que ça te convient et pose la question pour le faire passer à l'action ou aux constatations suivantes.
            Si le participant désire appeler les secours, tu joueras alors le rôle de l'interlocuteur. Tu pourras alors lui demander les informations nécessaires à la compréhension de la situation, des gestes réalisés, des données mesurées.
            Un dialogue peut s'installer avec le secouriste et des conseils peuvent être donnés. Pour cela, tu t'appuies sur les embeddings et notamment le "PSE guide pratique 2023" partie "transmission du bilan".
            Tu bases tes réponses et tes conseils sur le "PSE guide pratique 2023" notamment en t'appuyant sur les parties "conduite à tenir" afin de fournir des réponses crédibles et médicalement fiables.
            Si il manque des précisions et que après avoir demandé des précisions, si l'utilisateur ne te les donne pas, donne les lui en faisant référence aux embeddings et notamment le "PSE guide pratique 2023 ou au "CRF_Memento operationnel_2024_DEF"
            Tu mets fin à la simulation quand tu juges que la situation a été bien gérée, soit qu'elle ait été réglée par l'utilisateur, soit que les secours aient pris le relais. L'utilisateur peut également demander à mettre fin à la simulation de manière prématurée.
            Quand tu mets fin à la simulation, tu fais un petit récap de ce qui était bien répondu ou moins bien répondu par l'utilisateur, en orientant vers les parties des documents des embeddings qui auraient permis d'améliorer les réponses.
            """

def answer_llm(user_input):
    embeddings = st.session_state.get("embeddings", None)
    messages = st.session_state.get("messages", [])

    if not embeddings or not messages:
        return "Erreur : la simulation n'a pas été initialisée."

    response = query_llm_with_embeddings(user_input, embeddings, messages)
    return response

def start_simulation(category):
    query = f"propose moi une simulation guidée formative sur {category}"

    st.session_state["messages"] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query}
    ]
    st.session_state["conversation"] = []
    st.session_state["embeddings"] = []
    collection_names = ["PSE_fichesdecas", "CI_2022_CasConcrets", "guide_pedagogique_psc", "Guide_PSE", "CRF_Memento_operationnel"]  # Add other collections as needed

    # Get embeddings for each collection and accumulate them
    for collection_name in collection_names:
        embeddings = get_embeddings(query, collection_name)
        if embeddings:
            st.session_state["embeddings"].append(embeddings)
    # st.session_state["embeddings"] = get_embeddings(query, "PSE_fichesdecas")
    answer = query_llm_with_embeddings(query, st.session_state["embeddings"], st.session_state["messages"])
    st.session_state["conversation"].append(f"Chatbot : {answer}")
    st.session_state["messages"].append({"role": "assistant", "content": answer})

def display_conversation():
    conversation = st.session_state.get("conversation", [])
    for msg in conversation:
        if msg.startswith("Chatbot :"):
            st.markdown(f"""
            <div style='background-color:#f8d7da; padding:10px; border-radius:10px; margin:5px 0;'>
                🤖 <b>Chatbot :</b> {msg.replace("Chatbot :", "")}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='background-color:#d4edda; padding:10px; border-radius:10px; margin:5px 0; text-align:right;'>
                🧑 <b>Vous :</b> {msg}
            </div>
            """, unsafe_allow_html=True)

def handle_user_interaction():
    if "recording" not in st.session_state:
        st.session_state.recording = False
    if "transcribed_text" not in st.session_state:
        st.session_state.transcribed_text = ""
    user_input = st.text_input("Tapez un message...")
    if st.button("Envoyer"):
        if user_input.strip():
            st.session_state["conversation"].append(user_input)
            st.session_state["messages"].append({"role": "user", "content": user_input})
            answer = answer_llm(user_input)
            st.session_state["conversation"].append(f"Chatbot : {answer}")
            st.session_state["messages"].append({"role": "assistant", "content": answer})
            st.rerun()
        else:
            st.warning("Veuillez entrer un message.")
    if st.button("🎙 Record Voice"):
        if not st.session_state.recording:
            st.session_state.recording = True
            st.session_state.start_time = time.time()
            recording_flag["active"] = True
            filename = "output.wav"
            duration = 6
            st.info("🎙 Enregistrement en cours... Parlez maintenant")
            threading.Thread(target=record_audio, args=(filename, duration, recording_flag)).start()

    # Bouton pour arrêter et transcrire
    if st.button("⏹ Stop Recording"):
        recording_flag["active"] = False
        st.session_state.recording = False

        transcription_file = "last_transcription.txt"
        text = ""
        file_mtime_before = os.path.getmtime(transcription_file) if os.path.exists(transcription_file) else 0

        with st.spinner("⏳ Transcription en cours..."):
            timeout = 15  # secondes
            start = time.time()

            while time.time() - start < timeout:
                if os.path.exists(transcription_file):
                    file_mtime_after = os.path.getmtime(transcription_file)
                    if file_mtime_after > file_mtime_before:
                        with open(transcription_file, "r") as f:
                            text = f.read().strip()
                        if text:
                            break
                time.sleep(0.2)

        if text:
            st.session_state.transcribed_text = text
            st.success("Transcription terminée ✅")

            # Ajouter la transcription à la conversation comme un message utilisateur
            st.session_state["conversation"].append(text)
            st.session_state["messages"].append({"role": "user", "content": text})
            answer = answer_llm(text)
            st.session_state["conversation"].append(f"Chatbot : {answer}")
            st.session_state["messages"].append({"role": "assistant", "content": answer})
            st.experimental_rerun()
        else:
            st.warning("⚠️ Transcription non reçue à temps.")
        

def main():
    st.sidebar.title("Navigation")
    selected_page = st.sidebar.radio("Go to", ["RescueReady App"])
    
    if selected_page == "RescueReady App":
        st.title("Simulation")

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
            start_simulation(category)

        if st.session_state.get("simulation_started", False):
            display_conversation()
            handle_user_interaction()

        # st.subheader("Enregistrement vocal")
        # if st.button("Enregistrer un message vocal"):
        #     st.write("Enregistrement en cours... (Non implémenté)")