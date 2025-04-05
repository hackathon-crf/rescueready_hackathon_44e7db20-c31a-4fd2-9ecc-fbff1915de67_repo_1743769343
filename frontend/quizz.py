import streamlit as st

def display_quiz():
    st.title("RescueReady Quizz")

    questions = [
        {
            "question": "Quelle est la première étape à suivre lorsqu'on arrive sur une scène d'accident ?",
            "choices": ["A. Interroger les témoins", "B. Protéger la scène", "C. Examiner la victime", "D. Appeler les secours"],
            "correct_answer": "B. Protéger la scène"
        },
        {
            "question": "Que faire si une victime est inconsciente mais respire ?",
            "choices": ["A. Pratiquer un massage cardiaque", "B. Mettre la victime en position latérale de sécurité", "C. Donner de l'eau à la victime", "D. Attendre les secours"],
            "correct_answer": "B. Mettre la victime en position latérale de sécurité"
        },
        # Ajoutez d'autres questions ici...
    ]

    if "quiz_score" not in st.session_state:
        st.session_state.quiz_score = 0
    if "quiz_index" not in st.session_state:
        st.session_state.quiz_index = 0

    if st.session_state.quiz_index < len(questions):
        question = questions[st.session_state.quiz_index]
        st.write(f"Question {st.session_state.quiz_index + 1}/{len(questions)}: {question['question']}")
        user_answer = st.radio("Choisissez une réponse :", question["choices"])

        if st.button("Soumettre"):
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
