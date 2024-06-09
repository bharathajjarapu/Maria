from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferWindowMemory
import sys
import os
import json
load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-pro")

template = f"""You are Jarvis a joyful friendly assistant
c
Previous conversation:
{{chat_history}}

Instruction:
{{question}}

Response:"""

prompt = PromptTemplate.from_template(template)
memory = ConversationBufferWindowMemory(memory_key="chat_history", k=2)

conversation = LLMChain(
    llm=llm,
    prompt=prompt,
    verbose=False,
    memory=memory
)

def send_response(response):
    response_json = json.dumps({"result": response})
    print(response_json)
    sys.stdout.flush()

# Process input and generate responses
while True:
    user_input = sys.stdin.readline().strip()
    if not user_input:
        break

    result = conversation({"question": user_input})['text']
    max_chunk_length = 1000
    chunks = [result[i:i + max_chunk_length] for i in range(0, len(result), max_chunk_length)]
    send_response(chunks)