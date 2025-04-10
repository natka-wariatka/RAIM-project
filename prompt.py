def medically_relevant_response(user_input):
    medically_relevant = f"""
        Here is the prompt from user:
        ```
        {user_input}
        ```
        Your task is to find out if the message contains any medical symptoms, health issues,
        any kind of medical data. Any description of feeling unwell or being in pain. 
        if so then you should output only in `True` or `False`.
    """
    return medically_relevant

def medical_interview_response(user_input, history):
    medical_interview=f"""
        Here is the prompt from user:
    
        {user_input} and session history: {history}
        
        Your task is to act like medical assistant and you have to find out about user symptoms and other important medical data.
        You should ask follow up questions if necessary. Treat user with empathy and understanding. Don't answer too long though. 
        
        """
    return medical_interview

def diagnosis_possible_response(history):
    diagnosis_possible = f"""
        Here is the history of users answers:  
        
        {history}
    
        Your task is to analyse user answers and determinate whether there is enough to provide diagnosis and recommended specialist or not.
        Your should output only in `True` or `False`.
        """
    return diagnosis_possible

def diagnosis(history):
    diagnosis_response = f"""
        
        Here is the history of users answers:
        {history}
        
        Your task is to provide possible diagnosis with the percentage and recommended doctors. """
    return diagnosis_response