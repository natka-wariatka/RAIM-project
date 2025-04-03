from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from flask import Flask, request, render_template
import logging
import re


logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)

def format_output(text):
    return re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

def init_llama3():
    try:
        create_promt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a medical assistant, who needs to find out more about the symptoms of a patient."),
                ("user", "Question: {question}")
            ]
        )

        lamma_model = OllamaLLM(model="llama3.2")
        format_output = StrOutputParser()

        chatbot_pipeline = create_promt | lamma_model | format_output

        return chatbot_pipeline
    except Exception as e:
        logging.error(f"Failed to initialize chatbot pipeline: {e}")
        raise

chatbot_pipeline = init_llama3()

@app.route('/', methods=['GET', 'POST'])
def main():
    query_input = None
    output = None

    if request.method == 'POST':
        query_input = request.form.get('query_input')

        if query_input:
            try:
                response = chatbot_pipeline.invoke({'question': query_input})
                output: init_llama3(response)
                print(response)
            except Exception as e:
                logging.error(f"Failed to get response from chatbot: {e}")

    return render_template('index.html', query_input=query_input, output=output)

if __name__ == "__main__":
    app.run(debug=True)