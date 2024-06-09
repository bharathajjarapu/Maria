from langchain.prompts import PromptTemplate
from llamafiles import Llamafile
from langchain.memory import ConversationBufferWindowMemory
import sys
import os
import json

# Initialize Llamafile LLM
llm = Llamafile()

# Define the prompt template
template = """This is a conversation between User and Jarvis, a friendly chatbot. 
Jarvis is helpful, kind, honest, good at writing, and never fails to answer any requests immediately and with precision.

Previous conversation:
{chat_history}

User Message:
{question}

Jarvis Response:"""

prompt = PromptTemplate.from_template(template)
memory = ConversationBufferWindowMemory(memory_key="chat_history", k=2)

def generate_response(question):
    chat_history = memory.load_memory_variables({"chat_history": ""})["chat_history"]
    
    # Format the prompt with the chat history and user question
    formatted_prompt = prompt.format(chat_history=chat_history, question=question)
    
    # Generate the response using the LLM
    response = llm.invoke(formatted_prompt)
    return response

def send_response(response):
    response_json = json.dumps({"result": response})
    print(response_json)
    sys.stdout.flush()

while True:
    user_input = sys.stdin.readline().strip()
    if not user_input:
        break

    result = generate_response(user_input)
    max_chunk_length = 1000
    chunks = [result[i:i + max_chunk_length] for i in range(0, len(result), max_chunk_length)]
    send_response(chunks)
    memory.save_context({"question": user_input}, {"text": result})