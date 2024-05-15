import streamlit as st
import json
import os
from anthropic import AnthropicBedrock
from dotenv import load_dotenv

# Load JSON file
def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# Load environment variables
load_dotenv('.env')

aws_access_key = os.getenv('aws_access_key_id')
aws_secret_access_key = os.getenv('aws_secret_access_key')
aws_session_token = os.getenv('aws_session_token')
region = 'us-east-1'

# Function to query Claude
def ask_claude(messages):
    client = AnthropicBedrock(aws_access_key=aws_access_key,
                              aws_region=region, 
                              aws_secret_key=aws_secret_access_key, 
                              aws_session_token=aws_session_token)

    completion = client.messages.create(
        model="anthropic.claude-3-sonnet-20240229-v1:0",
        max_tokens=1024,
        messages=messages
    )

    return completion.content[0].text

# Main application
def main():
    st.set_page_config(page_title="Chemwatch SDS Chatbot", page_icon=":robot_face:")
    st.title("Chemwatch SDS Chatbot")
    st.sidebar.title("Chemicals")
    
    # List all the files in the files directory
    files = os.listdir("files")
    filenames = [file.split(".")[0] for file in files]

    # Create a dictionary to store the chemical name and its content
    chemical_content = {}
    # Load the content of each file
    for file in files:
        filename = file.split(".")[0]
        file_path = os.path.join("files", file)
        with open(file_path, 'r') as f:
            content = f.read()
            chemical_content[filename] = content

    st.sidebar.write("Select a chemical:")
    selected_chemical = st.sidebar.selectbox("Chemical", filenames)

    if selected_chemical:
        context = chemical_content[selected_chemical]
        # Initialize session state messages
        if 'messages' not in st.session_state:
            st.session_state.messages = []

        # Add initial context message if not already added
        if not st.session_state.messages:
            st.session_state.messages.append({
                "role": "user",
                "content": f"This is an SDS for {selected_chemical}. You will be asked questions about it. Please do not answer any questions outside of the SDS. Please keep your answers brief but not truncated. SDS: {context}"
            })
            st.session_state.messages.append({"role": "assistant", "content": f"Ask me anything about {selected_chemical}"})

        query = st.chat_input(f"Ask me anything about {selected_chemical}")

        if query:
            st.session_state.messages.append({"role": "user", "content": query})
            response = ask_claude(st.session_state.messages)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
    for message in st.session_state.messages[1:]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if __name__ == "__main__":
    main()
