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
    medical_interview=f"""
        The user described the following health issue:
    
        {user_input} and here are the previous answers: {history}
        
        Your task is to act like a friendly medical assistant.
        Generate 2 to 4 clear, medically relevant follow-up questions to gather more information. 
        The goal is to understand the user's symptoms better in terms of:
        - Duration and onset
        - Severity
        - Location
        - Accompanying symptoms
        - Relevant lifestyle or medical history
        Keep your questions medium length, don't use too long sentences. 
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
        
        Generate 3 to 4 most likely causes for the user's condition. Include:
        - A short name for the condition
        - Estimated likelihood as a percentage (add up to ~100%)
        - Short explanation (1–2 sentences)
        - Recommended type of medical specialist
        When suggesting a specialist, choose one from the following list only:
        {specialist_list}

        
        Respond in this format:
        
        1. Condition Name (XX%) - Explanation.
           Suggested Specialist: [Type of Specialist]
        """
    return diagnosis_response