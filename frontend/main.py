import streamlit as st
from pathlib import Path
from frontend.middleware import call_backend_test
from frontend.mistral import call_mistral
from frontend.RAG import get_embeddings, get_collections, query_llm_with_embeddings
from frontend.chatbot import display_chatbot
import requests


def call_llm(category):
    # collections = get_collections()
    # Select the first collection or use a default one
    collection_name = "PSE_fichesdecas"
    query = f"propose moi une simulation guidée formative sur {category}"
    embeddings = get_embeddings(query, collection_name)
    # context = {
    #     "situation": "Person has fallen from a ladder and is unconscious",
    #     "emergency_type": "Fall injury",
    #     "severity": "High",
    #     "age_group": "Adult"
    # }
    response = query_llm_with_embeddings(query, embeddings, None)
    return response

def answer_llm(user_input):
    collection_name = "PSE_fichesdecas"
    query = f"propose moi une simulation guidée formative sur {category}"
    embeddings = get_embeddings(query, collection_name)
    response = query_llm_with_embeddings(query, embeddings, None)
    return response

def main():
    # Create sidebar buttons
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
            answer = call_llm(category)
            st.session_state["conversation"] = [f"Chatbot : {answer}"]

        if st.session_state.get("simulation_started", False):
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
            user_input = st.text_input("Tapez un message...")
            if st.button("Envoyer"):
                if user_input.strip():
                    # Ajoute le message de l'utilisateur à la conversation
                    st.session_state["conversation"].append(user_input)
                    answer = answer_llm(user_input)

                else:
                    st.warning("Veuillez entrer un message.")

            # user_input = st.text_input("Tapez un message...")
            # if st.button("Envoyer"):
            #     print(user_input)
                # response = requests.post("http://127.0.0.1:8000/chat", json={"message": user_input})
                # if response.status_code == 200:
                #     st.write("Réponse du chatbot :", response.json()["response"])

        st.subheader("Enregistrement vocal")
        if st.button("Enregistrer un message vocal"):
            st.write("Enregistrement en cours... (Non implémenté)")


    
    # prompt = 'tu es une application pour remplacer les formateurs de la croix rouge. \
    # Tu dois proposer à l utilisateur des cas concrets sur la base des fiches de cas en ne lui donnant pas toutes les informations en meme temps mais au fur et a mesure de leur decouverte \
    # Par exemple, tu ne lui donne au depart que les informations pour lesquelles il a ete appele, \
    # puis tu lui fournis les informations visuelle qu il peut constater en arrivant sur place (en regardant la scene dans son ensemble) \
    # avant de lui fournir d autres informations de la fiche de cas tu lui demandes ce qu il ferait dans cette situation \
    # selon sa reponse tu lui donnes des information supplementaires. Par exemple s il te dit interroger les temoins, tu lui donnes les informations correspondantes. \
    # s il te dit prendre la tension, tu lui donnes l information correspondante puis tu attends sa prochaine action. \
    # Tu dois evaluer ses actions et son analyse sur la base de la partie evaluation de la fiche de cas"

    # st.subheader("Communication")
    # if "chat_history" not in st.session_state:
    #     st.session_state.chat_history = []
    
    # for msg in st.session_state.chat_history:
    #     st.markdown(f"{msg}")
    
    # st.subheader("💬 Envoyer une instruction")
    # user_input = st.text_input("Votre message :", key="user_prompt")
    
    # if st.button("(Mic)"):
    #     st.info("J'écoute...")
    #     vosk_model_path = "vosk-model-small-fr-0.22"
    #     if not os.path.exists(vosk_model_path):
    #         st.error(f"Model not found")
    
    # if st.button("Envoyer"):
    #     if user_input.strip():
    #         # Simule une réponse (à remplacer par appel backend plus tard)
    #         response = f"[Réponse simulée à]: {user_input}"
    #         st.session_state.chat_history.append(f"👤 Vous : {user_input}")
    #         st.session_state.chat_history.append(f"🤖 Assistant : {response}")
    #     else:
    #         st.warning("Veuillez entrer un message avant d'envoyer.")