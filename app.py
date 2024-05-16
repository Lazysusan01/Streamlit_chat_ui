import streamlit as st
import json
import os
from anthropic import AnthropicBedrock
from dotenv import load_dotenv
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from PIL import Image

session = boto3.Session(profile_name='nicomcgill')

def ask_claude(system_prompt,messages):
    try:
        # Retrieve temporary credentials from the session
        credentials = session.get_credentials()
        current_credentials = credentials.get_frozen_credentials()
        aws_access_key = current_credentials.access_key
        aws_secret_key = current_credentials.secret_key
        aws_session_token = current_credentials.token

        # Create the AnthropicBedrock client using the retrieved credentials
        client = AnthropicBedrock(
            aws_access_key=aws_access_key,
            aws_secret_key=aws_secret_key,
            aws_session_token=aws_session_token,
            aws_region='us-east-1'
        )

        # Stream messages
        with client.messages.stream(
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            max_tokens=1024,
            system=system_prompt,
            messages=messages
        ) as stream:
            for chunk in stream.text_stream:
                yield chunk

    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Error retrieving credentials: {e}")

def main():
    st.set_page_config(page_title="Chemwatch SDS Chatbot", page_icon=":robot_face:")
    sidebar_image = Image.open("CW_logo.png")
    st.sidebar.image(sidebar_image)
    st.title("Chemwatch SDS Chatbot :robot_face:")
    
    language = st.sidebar.selectbox("Select a language", ["English", "French", "Spanish", "Uwu","Pirate"])
    st.sidebar.title("Select a chemical or select two to compare:")
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
    
    # List all the files in the files directory
    files = os.listdir("files")
    filenames = [file.split(".")[0] for file in files if file.endswith(".json")]
    
    # create a dictionary to store the chemical name and its content
    chemical_content = {}
    # Load the content of each file
    for file in files:
        filename = file.split(".")[0]
        file_path = os.path.join("files", file)
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
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
            
        if len(selected_chemical) == 1:
            context = chemical_content[selected_chemical[0]]
            system_prompt = f"This is an SDS for {selected_chemical}, you will be asked questions about it, please do not answer any questions outside of the sds, please keep your answer brief but not truncated, respond only in {language}. <SDS>{context}</SDS>"
            query = st.chat_input(f"Ask me anything about {selected_chemical[0]}")
            # st.session_state.messages.append({"role": "assistant", "content": f"Ask me anything about {selected_chemical}"})
        elif len(selected_chemical) == 2:
            chemical1 = chemical_content[selected_chemical[0]]
            chemical2 = chemical_content[selected_chemical[1]]
            system_prompt = f"These are SDS for {selected_chemical[0]} and {selected_chemical[1]}, you will be asked questions about them, please do not answer any questions outside of the sds, please keep your answer brief but not truncated, respond only in {language}. <SDS1>{chemical1}</SDS1> <SDS2>{chemical2}</SDS2>"
            query = st.chat_input(f"Ask me anything about {selected_chemical[0]} and {selected_chemical[1]}")
            # st.session_state.messages.append({"role": "assistant", "content": f"Ask me anything about {selected_chemical[0]} and {selected_chemical[1]}"})
        
        if query:
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.markdown(query)
            response = st.write_stream(ask_claude(system_prompt, st.session_state.messages))
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()