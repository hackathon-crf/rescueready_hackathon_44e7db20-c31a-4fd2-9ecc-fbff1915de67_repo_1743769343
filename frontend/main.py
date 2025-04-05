import streamlit as st
from pathlib import Path
from frontend.middleware import call_backend_test
from frontend.mistral import call_mistral
from frontend.RAG import get_embeddings, get_collections, query_llm_with_embeddings
from frontend.chatbot import display_chatbot
import requests

SYSTEM_PROMPT = """
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
    collection_names = ["PSE_fichesdecas", "CI_2022_CasConcrets", "guide_pedagogique_psc", "CRF_Memento_operationnel"]  # Add other collections as needed

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

        st.subheader("Enregistrement vocal")
        if st.button("Enregistrer un message vocal"):
            st.write("Enregistrement en cours... (Non implémenté)")