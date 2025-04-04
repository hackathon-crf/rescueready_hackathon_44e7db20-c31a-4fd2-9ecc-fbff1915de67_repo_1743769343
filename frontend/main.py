import streamlit as st
from pathlib import Path
from frontend.middleware import call_backend_test
from frontend.mistral import call_mistral
from frontend.RAG import get_embeddings, get_collections
# query_llm_with_embeddings, 

def main():
    # Create sidebar buttons
    st.sidebar.title("Navigation")
    selected_page = st.sidebar.radio("Go to", ["RescueReady App"])
    
    if selected_page == "RescueReady App":
        st.header("Welcome to the RescueReady Application")
        game()
        # backend_response = call_backend_test()
        # if backend_response:
        #     st.success(backend_response.get("message"))
        #     st.write("Data")
        #     data = backend_response.get("data")
        #     st.write(data)
        # else:
        #     st.error('Backend is not responding')


def game():
    st.title("Simulation")
    st.subheader("Contexte")
    
    collections = get_collections()
    # Select the first collection or use a default one
    # collection_name = "guide_pedagogique_psc"
    # Sample emergency context
    query = "propose moi une simulation guidée formative sur les traumatismes"
    embeddings = get_embeddings(query, collections)
    # Select the first collection or use a default one

    # Sample emergency context
    # context = {
    #     "situation": "Person has fallen from a ladder and is unconscious",
    #     "emergency_type": "Fall injury",
    #     "severity": "High",
    #     "age_group": "Adult"
    # }
    # query_llm_with_embeddings(query, embeddings, context)

    response = call_mistral()

    st.markdown(f"""
        **Contexte** : {response}
    
        **Objectif** : Interagir avec un agent conversationnel.
    
        **Contraintes** : Matériel ..., priorisation ..., stress ... .
    """
    )



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