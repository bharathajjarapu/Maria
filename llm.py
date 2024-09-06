from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import LlamaCpp
from langchain.memory import ConversationBufferWindowMemory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from PyPDF2 import PdfReader
import sys
import json
import os
import io

def extract_text_from_pdf(file_bytes):
    text = ""
    pdf_io = io.BytesIO(file_bytes)
    pdf_reader = PdfReader(pdf_io)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def split_text_into_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    text_chunks = text_splitter.split_text(text)
    return text_chunks

def create_vector_store(chunks, pdf_name):
    embeddings = HuggingFaceEmbeddings()
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    vector_store.save_local(f"vector_stores/{pdf_name}")
    return vector_store

def setup_conversational_chain(llm):
    template = """You are Jarvis, a helpful and honest assistant. Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

    Context:
    {context}

    Previous conversation:
    {chat_history}

    Question: {question}

    Answer:"""
    prompt = PromptTemplate(template=template, input_variables=["context", "chat_history", "question"])
    memory = ConversationBufferWindowMemory(memory_key="chat_history", k=2)
    return LLMChain(llm=llm, prompt=prompt, verbose=False, memory=memory)

def get_pdf_list():
    if not os.path.exists("vector_stores"):
        os.makedirs("vector_stores")
    return [f for f in os.listdir("vector_stores") if f.endswith(".faiss")]

def delete_pdf(filename):
    base_filename = os.path.splitext(filename)[0]
    faiss_file = os.path.join("vector_stores", f"{base_filename}.faiss")
    index_file = os.path.join("vector_stores", f"{base_filename}.pkl")
    
    if os.path.exists(faiss_file):
        os.remove(faiss_file)
    if os.path.exists(index_file):
        os.remove(index_file)

def main():
    p = os.path.join(os.path.expanduser("~"), "Documents", "LLM")
    if not os.path.exists(p):
        print('LLM NOT FOUND!')
        os.makedirs(p)
    m_path = os.path.join(p, "MLP.gguf")

    llm = LlamaCpp(
        model_path=m_path,
        n_gpu_layers=-1,
        n_batch=256,
        f16_kv=True,
        max_tokens=500,
        temperature=0.7,
        n_ctx=4000,
    )

    conv_chain = setup_conversational_chain(llm)
    vector_stores = {}

    def send_response(r, response_type='message'):
        print(json.dumps({"type": response_type, "result": r}))
        sys.stdout.flush()

    while True:
        input_data = json.loads(sys.stdin.readline().strip())
        if input_data['type'] == 'message':
            user_input = input_data['content']
            context = ""
            for pdf_name, vector_store in vector_stores.items():
                relevant_docs = vector_store.similarity_search(user_input, k=2)
                context += f"\nContext from {pdf_name}:\n" + "\n".join([doc.page_content for doc in relevant_docs])
            
            response = conv_chain({"context": context, "question": user_input})['text']
            chunks = [response[i:i + 1000] for i in range(0, len(response), 1000)]
            send_response(chunks)
        elif input_data['type'] == 'pdf_upload':
            file_bytes = bytes(input_data['content'])
            filename = input_data['filename']
            text = extract_text_from_pdf(file_bytes)
            chunks = split_text_into_chunks(text)
            vector_store = create_vector_store(chunks, filename)
            vector_stores[filename] = vector_store
            send_response(filename, 'pdf_processed')
            send_response(get_pdf_list(), 'pdf_list')
        elif input_data['type'] == 'delete_pdf':
            filename = input_data['filename']
            delete_pdf(filename)
            if filename in vector_stores:
                del vector_stores[filename]
            send_response(filename, 'pdf_deleted')
            send_response(get_pdf_list(), 'pdf_list')
        elif input_data['type'] == 'get_pdf_list':
            send_response(get_pdf_list(), 'pdf_list')

if __name__ == "__main__":
    main()