import streamlit as st
from frontend.RAG import get_embeddings, get_collections, query_llm_with_embeddings
import ast  # Ajoutez cette ligne pour importer le module ast

SYSTEM3_PROMPT = "Tu es une application qui propose des quizz pour accompagner les bénévoles de la Croix Rouge \
                dans leur formation aux premiers secours. Tu proposeras un quizz de 5 questions avec 4 choix \
                possibles mais 1 seule réponse correcte, sur la base des documents inclus en Embedding, et qui \
                compte les points sur 5 et donne le score a la fin des 5 questions. \
				retourne une chaîne de caractères représentant une liste de dictionnaires avec la structure: question: ..., choices: ..., correct_answer: ..."

def start_quizz(category):
    query = f"propose moi un quizz sur {category}"

    st.session_state["messages"] = [
        {"role": "system", "content": SYSTEM3_PROMPT},
        {"role": "user", "content": query}
    ]
    st.session_state["embeddings"] = []
    collection_names = ["PSE_fichesdecas", "CI_2022_CasConcrets", "guide_pedagogique_psc", "Guide_PSE", "CRF_Memento_operationnel"]

    # Get embeddings for each collection and accumulate them
    for collection_name in collection_names:
        embeddings = get_embeddings(query, collection_name)
        if embeddings:
            st.session_state["embeddings"].append(embeddings)

    answer = query_llm_with_embeddings(query, st.session_state["embeddings"], st.session_state["messages"])
    # Assuming the answer contains the questions in a structured format
    questions = parse_questions_from_response(answer)
    print("ICI")
    print(questions)
    st.session_state["questions"] = questions
    st.session_state["quiz_score"] = 0
    st.session_state["quiz_index"] = 0

def parse_questions_from_response(response):
    try:
        # Extraire le contenu du bloc de code de la réponse
        code_block_start = response.find("question")
        code_block_end = response.find("```", code_block_start)
        code_block = response[code_block_start:code_block_end].strip()
        code_block2 = '[{"' + code_block
        print('code block = ', code_block2)
        # Évaluer le code Python pour obtenir la liste de dictionnaires
        # questions_list = ast.literal_eval(code_block)
        return code_block2
    except (SyntaxError, ValueError):
        # Gérer les erreurs si la réponse n'est pas dans le format attendu
        st.error("Erreur lors de l'analyse de la réponse du modèle.")
        return []

def display_quiz(categories):
    st.title("RescueReady Quizz")
    category = st.selectbox("Choisissez une catégorie", list(categories.values()))
    if st.button("Démarrer le quizz"):
        st.session_state["simulation_started"] = True
        start_quizz(category)

    if st.session_state.get("simulation_started", False):
        questions = st.session_state.get("questions", [])

        if st.session_state.quiz_index < len(questions):
            question = questions[st.session_state.quiz_index]
            st.write(f"Question {st.session_state.quiz_index + 1}/{len(questions)}: {question['question']}")
            user_answer = st.radio("Choisissez une réponse :", question["choices"])

            if st.button("Valider"):
                if user_answer == question["correct_answer"]:
                    st.session_state.quiz_score += 1
                st.session_state.quiz_index += 1
                st.experimental_rerun()
        else:
            st.write(f"Votre score est de {st.session_state.quiz_score}/{len(questions)}")
            if st.button("Recommencer le quiz"):
                st.session_state.quiz_score = 0
                st.session_state.quiz_index = 0
                st.experimental_rerun()



# 
# 
#  import streamlit as st
# from frontend.RAG import get_embeddings, get_collections, query_llm_with_embeddings

# SYSTEM3_PROMPT = "Tu es une application qui propose des quizz pour accompagner les bénévoles de la Croix Rouge dans leur formation aux premiers secours. \
# Tu proposeras un quizz de 10 questions avec 4 choix possibles mais 1 seule réponse correcte, sur la base des documents inclus en Embedding, et qui compte les points sur 10 et donne le score a la fin des 10 questions."

# def start_quizz(category):
#     query = f"propose moi un quizz sur {category}"

#     st.session_state["messages"] = [
#         {"role": "system", "content": SYSTEM3_PROMPT},
#         {"role": "user", "content": query}
#     ]
#     st.session_state["embeddings"] = []
#     collection_names = ["PSE_fichesdecas", "CI_2022_CasConcrets", "guide_pedagogique_psc", "Guide_PSE", "CRF_Memento_operationnel"]  # Add other collections as needed

#     # Get embeddings for each collection and accumulate them
#     for collection_name in collection_names:
#         embeddings = get_embeddings(query, collection_name)
#         if embeddings:
#             st.session_state["embeddings"].append(embeddings)
#     answer = query_llm_with_embeddings(query, st.session_state["embeddings"], st.session_state["messages"])
#     print(answer)

# def display_quiz(categories):
#     st.title("RescueReady Quizz")
#     category = st.selectbox("Choisissez une catégorie", list(categories.values()))
#     if st.button("Démarrer le quizz"):
#         st.session_state["simulation_started"] = True
#         questions = start_quizz(category)
#         print(questions)
    
#     # if "quiz_score" not in st.session_state:
#     #     st.session_state.quiz_score = 0
#     # if "quiz_index" not in st.session_state:
#     #     st.session_state.quiz_index = 0

#     # if st.session_state.quiz_index < len(questions):
#     #     question = questions[st.session_state.quiz_index]
#     #     st.write(f"Question {st.session_state.quiz_index + 1}/{len(questions)}: {question['question']}")
#     #     user_answer = st.radio("Choisissez une réponse :", question["choices"])

#     #     if st.button("Soumettre"):
#     #         if user_answer == question["correct_answer"]:
#     #             st.session_state.quiz_score += 1
#     #         st.session_state.quiz_index += 1
#     #         st.experimental_rerun()
#     # else:
#     #     st.write(f"Votre score est de {st.session_state.quiz_score}/{len(questions)}")
#     #     if st.button("Recommencer le quiz"):
#     #         st.session_state.quiz_score = 0
#     #         st.session_state.quiz_index = 0
#     #         st.experimental_rerun()
