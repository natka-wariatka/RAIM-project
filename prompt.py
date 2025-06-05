def medically_relevant_response(user_input):
    medically_relevant = f"""
        Here is the prompt from user:
        ```
        {user_input}
        ```
        Determine whether the user's input is medically relevant.
        output only in `True` if it is medically relevant or `False` if it is not.
    """
    return medically_relevant

def medical_interview_response(user_input, history):
    medical_interview = f"""
        The user described the following health issue:
        
        {user_input} and here are the previous answers: {history}
        
        Your task is to act like a friendly and thorough medical assistant.
        Generate medically relevant follow-up questions to gather more information.
        Take into consideration the previous answers. If there is an "intro text" in the history session, focus on the medical data provided.
        
        Your goals are:
        - Clarify existing symptoms (e.g. duration, onset, severity, location, accompanying symptoms, lifestyle/medical history).
        - Explore common related symptoms that the user has not yet mentioned but may be relevant based on the initial description (e.g. in case of fever and chills, ask also about cough, sore throat, or muscle aches).
        - Help identify possible patterns and rule out other conditions.
        
        Keep your questions medium length. Don't use overly long sentences.
        Ask up to 3 follow-up questions. Include both clarifying and exploratory questions.
        """
    return medical_interview


def diagnosis_possible_response(history):
    diagnosis_possible = f"""
        Here is the history of users answers:  

        {history}

        Decide if there is enough information to suggest possible causes of the health issues.
        Your should output only in `True` or `False`.
        """
    return diagnosis_possible


def diagnosis(history, specialist_list):
    diagnosis_response = f"""

        Here is the history of users answers:
        {history}

        Generate 3 most likely causes for the user's condition. Include:
        - A short name for the condition
        - Estimated likelihood as a percentage (add up to ~100%)
        - Short explanation (1–2 sentences)
        - Recommended type of medical specialist
        When suggesting a specialist, choose one from the following list only:
        {specialist_list}


        Respond in this format:

        1. Condition Name (XX%) - Explanation.
           Suggested Specialist: [Type of Specialist]
           
        2. Condition Name (XX%) - Explanation.
           Suggested Specialist: [Type of Specialist]
        
        3. Condition Name (XX%) - Explanation.
           Suggested Specialist: [Type of Specialist]
        """
    return diagnosis_response