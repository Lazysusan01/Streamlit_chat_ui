import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
# import sys
# sys.path.append(r'C:\Users\nico_chemwatch\OneDrive - Ucorp Pty Ltd T A Chemwatch\Documents\Streamlit_chat_ui\Homepage.py')
from Homepage import get_credentials, ask_claude

from PIL import Image

st.set_page_config(page_title="PDF Uploader", page_icon=":file_folder:", layout="wide")
# upload pdf button 
col1, col2= st.columns([0.6,0.4])
sidebar_image = Image.open("CW_logo.png")
st.sidebar.image(sidebar_image)
# Select Language and chemicals
language = st.sidebar.selectbox("Select a language", ["English", "French", "Spanish", "Uwu","Pirate"])
# Styling the sidebar
sidebar_styles = """
/* Sidebar styles */
[data-testid="stSidebar"] > div {
    background-color: #C2DBFF;
    color: white;
}
    [data-testid="stSidebar"] img {
    width: 200px;
    height: auto;
    align: center;
}
"""
st.markdown(f"<style>{sidebar_styles}</style>", unsafe_allow_html=True)
with col1:
    st.header("Upload PDF")
    pdf_file = st.file_uploader("Upload a PDF file", type=["pdf"])    
    if pdf_file is not None:
        # display pdf file
        pdf_viewer(pdf_file.read())
    
with col2.container(height=800):
    st.header("PDF Chatbot")
    with st.chat_message("assistant"):
        st.write("Welcome to the Chemwatch SDS Chatbot. Please select a chemical(s).")

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.credentials = get_credentials()
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    if pdf_file is not None:           
        suggested_queries = ['What are the hazards of this chemical?',
                            'What are the first aid measures for this chemical?',
                            'What are the physical properties of this chemical?', 
                            'What are the storage and handling instructions for this chemical?']
        
        system_prompt = f"""you will be asked questions about it, please do not answer any questions outside of the sds,
                            Do not mention the R codes directly as they are internal codes, just give the description please.
                            Regulatory burdens translate to: 1: Lightly regulated, 2: Moderately regulated, 3: Highly regulated, 4: Highly regulated, 5: Extremely regulated.
                            Handling instructions can be inferred from defaultPpeimages but do not mention the images directly.
                            The current inventory status is in 'manifest' under 'cur'.
                            Where applicable, please provide the information as a table.                                 
                            Please respond only in {language}. <SDS>{pdf_file}</SDS>"""
        query = st.chat_input(f"Ask me anything about this PDF")

        query_placeholder = st.empty()
        for question in suggested_queries: 
            if st.button(question):
                query = question
                
        if query:
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.markdown(query)
            
            response = st.write_stream(ask_claude(system_prompt, st.session_state.messages, credentials=st.session_state.credentials))
            st.session_state.messages.append({"role": "assistant", "content": response})