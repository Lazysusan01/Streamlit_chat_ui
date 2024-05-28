import streamlit as st
import json
import os
from anthropic import AnthropicBedrock
from dotenv import load_dotenv
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from PIL import Image

def get_credentials():
    try:
        #     try:
        session = boto3.Session(profile_name='nicomcgill')
        # Retrieve temporary credentials from the session
        credentials = session.get_credentials()
        current_credentials = credentials.get_frozen_credentials()
        if current_credentials:
            print("Using AWS credentials from the session profile")
        return {
            "aws_access_key": current_credentials.access_key,
            "aws_secret_key": current_credentials.secret_key,
            "aws_session_token": current_credentials.token,
        }
    except:
        load_dotenv()
        aws_access_key = os.getenv("aws_access_key_id")
        aws_secret_key = os.getenv("aws_secret_access_key")
        aws_session_token = os.getenv("aws_session_token")
        if aws_access_key:
            print("Using AWS credentials from the environment variables")
        return {
            "aws_access_key": aws_access_key,
            "aws_secret_key": aws_secret_key,
            "aws_session_token": aws_session_token,
        }

def ask_claude(system_prompt, messages, credentials):
#   get_boto3_credentials() or
    # Create the AnthropicBedrock client using the retrieved credentials
    client = AnthropicBedrock(
        aws_access_key=credentials["aws_access_key"],
        aws_secret_key=credentials["aws_secret_key"],
        aws_session_token=credentials["aws_session_token"],
        aws_region='us-west-2'
    )

    # Stream messages
    with client.messages.stream(
        model="anthropic.claude-3-opus-20240229-v1:0",
        max_tokens=1024,
        system=system_prompt,
        messages=messages
    ) as stream:
        for chunk in stream.text_stream:
            yield chunk

def main():
    st.set_page_config(page_title="Chemwatch SDS Chatbot", page_icon=":robot_face:")
    st.title("Chemwatch SDS Chatbot :robot_face:")
    # Chemwatch logo in sidebar
    sidebar_image = Image.open("CW_logo.png")
    st.sidebar.image(sidebar_image)
    # Select Language and chemicals
    language = st.sidebar.selectbox("Select a language", ["English", "French", "Spanish", "Uwu","Pirate"])
    st.sidebar.title("Select a chemical or select two to compare:")
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
    
    file_location = 'files/MiniSDS/'
    # List all the files in the files directory
    files = os.listdir(file_location)
    filenames = [file.split(".")[0] for file in files if file.endswith(".json")]
    
    # create a dictionary to store the chemical name and its content
    chemical_content = {}
    # Load the content of each file
    for file in files:
        filename = file.split(".")[0]
        file_path = os.path.join(file_location, file)
        # print(file, filename, file_path)
        with open(file_path, 'r') as f:
            content = f.read()
            chemical_content[filename] = content    
    
    with st.chat_message("assistant"):
        st.write("Welcome to the Chemwatch SDS Chatbot. Please select a chemical(s).")
        
    selected_chemical = st.sidebar.multiselect("Chemical(s)", filenames, max_selections=2)
    
    if selected_chemical:
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        credentials = get_credentials()
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
            
        if len(selected_chemical) == 1:
            
            suggested_queries = ['What are the hazards of this chemical?',
                                'What are the first aid measures for this chemical?',
                                'What are the physical properties of this chemical?', 
                                'What are the storage and handling instructions for this chemical?']
            
            context = chemical_content[selected_chemical[0]]
            system_prompt = f"""This is an SDS for {selected_chemical}, you will be asked questions about it, please do not answer any questions outside of the sds,
                                Do not mention the R codes directly as they are internal codes, just give the description please.
                                Definitions:

                                SDS:
                                SDS or MSDS Safety data sheets (SDS) are important documents that provide critical information about hazardous chemicals, their properties,
                                and the measures that should be taken to ensure safe handling and use. They are an essential component of a company's chemical management program
                                and are required by law in many countries.

                                ILO RA:
                                The International Labour Organisation (ILO) has developed a Risk Assessment Model described as "Control Banding" It is based on the Model developed 
                                by the UK HSE known as CosshEssentials. Both Agencies adopt the Globally Harmonised System (GHS) for determining chemical hazards. National or Regional
                                variants exist- CLP in Europe and China, HSIS in Australia
                                
                                UN RA:
                                The United Nations (UN) Dangerous Goods Codes have been developed to regulate Transport and Storage of chemicals on Land. Similar systems have been 
                                adopted for Air (IATA) and Water (IMDG) Transport and Storage. Various countries / jurisdictions have local variants (e.g ADG in Australia, DOT in the USA, ADR throughout Europe)
                                
                                Regulatory burdens translate to: 1: Lightly regulated, 2: Moderately regulated, 3: Highly regulated, 4: Highly regulated, 5: Extremely regulated.
                                Handling instructions can be inferred from defaultPpeimages but do not mention the images directly.
                                The current inventory status is in 'manifest' under 'cur'.
                                Where applicable, please provide the information as a table.
                                Please respond only in {language}. <SDS>{context}</SDS>"""
                                
            query = st.chat_input(f"Ask me anything about {selected_chemical[0]}")
            # st.session_state.messages.append({"role": "assistant", "content": f"Ask me anything about {selected_chemical}"})
        elif len(selected_chemical) == 2:
            suggested_queries = ['What are the differences between these two chemicals? (format your answer as a table)',
                                 'What are the first aid measures for these two chemicals?',
                                 'What are the physical properties of these two chemicals?',
                                 'What are the storage and handling instructions for these two chemicals?']

            chemical1 = chemical_content[selected_chemical[0]]
            chemical2 = chemical_content[selected_chemical[1]]
            system_prompt = f"These are SDS for {selected_chemical[0]} and {selected_chemical[1]}, you will be asked questions about them, please do not answer any questions outside of the sds, please keep your answer brief but not truncated, respond only in {language}. <SDS1>{chemical1}</SDS1> <SDS2>{chemical2}</SDS2>"
            query = st.chat_input(f"Ask me anything about {selected_chemical[0]} and {selected_chemical[1]}")

        query_placeholder = st.empty()
        for question in suggested_queries: 
            if st.button(question):
                query = question
                
        if query:
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.markdown(query)
                
            response = st.write_stream(ask_claude(system_prompt, st.session_state.messages, credentials=credentials))
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()