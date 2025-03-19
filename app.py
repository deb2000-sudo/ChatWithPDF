import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

# Google Generative AI (Gemini) embeddings and chat model
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI

# Google Generative AI SDK
import google.generativeai as genai  

# FAISS Vector Store
from langchain_community.vectorstores import FAISS  

# LangChain QA Chain & Prompt Template
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate

# Load environment variables
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


#GET PDF TEXT from all pdfs
def get_pdf_text(pdf_docs):
    text=""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

#divide text into chunks
def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000,chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

#get verctor store for chnuks

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embeddings)
    vector_store.save_local("faiss_index")
    return vector_store

def get_conversational_chain():
    prompt_template='''
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    the provided conext just say, "answer is not available in the context", don't provide the wrong answer.
    Context:\n{context}?\n
    Question:\n{question}\n
    
    Answer:
    
    '''
    model=ChatGoogleGenerativeAI(model="gemini-2.0-flash",temperature=0.3)
    
    prompt=PromptTemplate(template=prompt_template,input_variables=["context","question"])
    chain=load_qa_chain(model,chain_type="stuff",prompt=prompt)
    return chain

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question)
    chain = get_conversational_chain()
    
    response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
    
    st.subheader("Answer:")
    st.write(response.get("output_text", "No response generated."))
    
def main():
    st.set_page_config(page_title="Chat  with multiple PDF",page_icon="📚")
    st.header("Chat with multiple  PDF using Gemini")
    
    user_question=st.text_input("Ask a Question from the PDF files")
    
    if user_question:
        user_input(user_question)
        
    with st.sidebar:
        st.title("Menu:")
        pdf_docs = st.file_uploader("Upload your PDF files and Click on the submit and process", 
                                   accept_multiple_files=True,
                                   type=['pdf'])
        if st.button("Submit & Process"):
            if pdf_docs:
                with st.spinner("Processing the pdf files"):
                    raw_text = get_pdf_text(pdf_docs)
                    text_chunks = get_text_chunks(raw_text)
                    get_vector_store(text_chunks)
                    st.success("Done")
            else:
                st.error("Please upload PDF files first")
                
                
                
if __name__=="__main__":
    main()