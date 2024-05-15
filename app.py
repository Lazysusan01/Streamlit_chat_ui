import streamlit as st
import json
import os
from anthropic import AnthropicBedrock
from dotenv import load_dotenv
import boto3

def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

load_dotenv('.env')

aws_access_key=os.getenv('aws_access_key_id')
aws_secret_access_key = os.getenv('aws_secret_access_key')
aws_session_token = os.getenv('aws_session_token')
region = 'us-east-1'

# session = boto3.Session(profile_name='nicomcgill')
# session.resource('Bedrock'  , region_name='us-east-1')

def ask_claude(messages):
       
    client = AnthropicBedrock(aws_access_key=aws_access_key,
                              aws_region=region, 
                              aws_secret_key=aws_secret_access_key, 
                              aws_session_token=aws_session_token)

    with client.messages.stream(
        model="anthropic.claude-3-sonnet-20240229-v1:0",
        max_tokens=1024,
        messages=messages,
    ) as stream:
        for chunk in stream.text_stream:
            yield chunk
    

          
    # input_tokens = completion.usage.input_tokens
    # output_tokens = completion.usage.output_tokens
    
    # total_cost = total_cost = input_tokens*0.000003 + output_tokens*0.000015
    # print(total_cost)

def main():
    st.set_page_config(page_title="Chemwatch SDS Chatbot", page_icon=":robot_face:")
    st.title("Chemwatch SDS Chatbot")
    
    st.sidebar.title("Select a chemical or select two to compare:")
    # st.sidebar.
    
    
    # List all the files in the files directory
    files = os.listdir("files")
    filenames = [file.split(".")[0] for file in files]
    
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
        st.write("Welcome to the Chemwatch SDS Chatbot. Please select a chemical(s) in the sidebar to compare.")
        
    selected_chemical = st.sidebar.multiselect("Chemical(s)", filenames, max_selections=2)
    if selected_chemical:
        st.session_state.messages = []
        if len(selected_chemical) == 1:
            context = chemical_content[selected_chemical[0]]
            st.session_state.messages.append({"role": "user", "content": f"This is an SDS for {selected_chemical}, you will be asked questions about it, please do not answer any questions outside of the sds, please keep your answer brief but not truncated. SDS: {context}"})
            query = st.chat_input(f"Ask me anything about {selected_chemical[0]}")
            st.session_state.messages.append({"role": "assistant", "content": f"Ask me anything about {selected_chemical}"})
        elif len(selected_chemical) == 2:
            chemical1 = chemical_content[selected_chemical[0]]
            chemical2 = chemical_content[selected_chemical[1]]
            st.session_state.messages.append({"role": "user", "content": f"These are SDS for {selected_chemical[0]} and {selected_chemical[1]}, you will be asked questions about them, please do not answer any questions outside of the sds, please keep your answer brief but not truncated. SDS 1: {chemical1}, SDS 2: {chemical2}"})
            query = st.chat_input(f"Ask me anything about {selected_chemical[0]} and {selected_chemical[1]}")
            st.session_state.messages.append({"role": "assistant", "content": f"Ask me anything about {selected_chemical[0]} and {selected_chemical[1]}"})
        
        if query:
            with st.chat_message("user"):
                st.markdown(query)
            st.session_state.messages.append({"role": "user", "content": query})
            st.write_stream(ask_claude(st.session_state.messages))

if __name__ == "__main__":
    main()