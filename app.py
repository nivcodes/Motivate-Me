import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.core import Root
import json


# Initialize Snowflake session and Cortex Search service
session = get_active_session()
root = Root(session)

# Define Cortex Search service parameters
CORTEX_SEARCH_DATABASE = "MOTIVATE_ME_DB"
CORTEX_SEARCH_SCHEMA = "APP_DATA"
CORTEX_SEARCH_SERVICE = "CC_SEARCH_SERVICE_CS"
NUM_CHUNKS = 3  # Number of chunks to retrieve for context

# Access the Cortex Search service
svc = root.databases[CORTEX_SEARCH_DATABASE].schemas[CORTEX_SEARCH_SCHEMA].cortex_search_services[CORTEX_SEARCH_SERVICE]

# Function to retrieve similar chunks from the search service
def get_similar_chunks(query):
    response = svc.search(query, ["chunk"], limit=NUM_CHUNKS)
    return response.json()

# Function to create the prompt for the LLM
def create_prompt(name, challenge, accomplishment, style):
    context = get_similar_chunks(challenge)
    
    if style == "Enthusiastic Hype Man":
        prompt = f"""
        You are an enthusiastic and supportive hype man. Using the CONTEXT 
        provided between <context> and </context> tags, generate a motivational 
        message for {name}, who is facing the following challenge: "{challenge}". 
        Also, acknowledge their accomplishment: "{accomplishment}". Be uplifting 
        and positive. Tell them they CAN do it. Use CAPS, emojis, and get them 
        excited!!! Use context where it makes sense (e.g., avoid mentioning 
        names that {name} may not recognize). Keep the response to 150 words 
        to make every word count. Sign your message as the Enthusiastic Hype Man.

        <context>
        {context}
        </context>
        """
    elif style == "Warm Encourager":
        prompt = f"""
        You are a warm and supportive friend. Using the CONTEXT 
        provided between <context> and </context> tags, generate a gentle and 
        encouraging message for {name}, who is facing the following challenge: 
        "{challenge}". Also, acknowledge their accomplishment: "{accomplishment}". 
        Be positive and reassuring. Use kind words and a comforting tone, along 
        with soft, kind emojis to help them feel soothed and confident. Use context
        where it makes sense (e.g., avoid mentioning names that {name} may not 
        recognize). Keep the response to 150 words to make every word count. Sign
        your message as the Warm Encourager.

        <context>
        {context}
        </context>
        """
    elif style == "Stoic Performer":
        prompt = f"""
        You are a calm and rational stoic mentor. Using the CONTEXT 
        provided between <context> and </context> tags, generate an empowering 
        message for {name}, who is facing the following challenge: "{challenge}". 
        Also, acknowledge their accomplishment: "{accomplishment}". Emphasize 
        resilience, self-control, and inner strength. Use concise and thoughtful 
        language to instill confidence. Use context where it makes sense 
        (e.g., avoid mentioning names that {name} may not recognize). Keep the 
        response to 150 words to make every word count. Sign your message as
        The Stoic Performer.

        <context>
        {context}
        </context>
        """
    return prompt

# Function to generate the motivational message
def generate_message(name, challenge, accomplishment, style):
    prompt = create_prompt(name, challenge, accomplishment, style)
    model_name = "mistral-large"  # You can choose other models as needed
    query = "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS response"
    df_response = session.sql(query, params=[model_name, prompt]).collect()
    return df_response[0].RESPONSE

# Streamlit app layout
st.title("AI-Powered Hype Man 🎉")
st.write("Welcome to your personal hype session! Ready to feel like a superstar?")

# User input form
with st.form(key='hype_form'):
    name = st.text_input("What's your name?", placeholder="Enter your name here")
    challenge = st.text_area("What are you struggling with?", placeholder="Describe your challenge here")
    accomplishment = st.text_area("What is something you're proud of?", placeholder="Share an accomplishment here")
    style = st.radio("Choose your motivational style:", ("Enthusiastic Hype Man", "Warm Encourager", "Stoic Performer"))
    submit_button = st.form_submit_button(label='Hype me up!')

# Generate and display the motivational message
if submit_button and name and challenge and accomplishment:
    if style == "Enthusiastic Hype Man":
        loading_message = 'Generating your hype... 🔥 You’re going to love this!'
    elif style == "Warm Encourager":
        loading_message = 'Generating a warm encouragement to support you... ☺️'
    elif style == "Stoic Performer":
        loading_message = 'Composing a stoic message to empower you... 🧘‍♂️'

    with st.spinner(loading_message):
        message = generate_message(name, challenge, accomplishment, style)
        st.success(message)
        st.balloons()
else:
    st.info("Please enter your name, the challenge you're facing, and something you're proud of to receive your personalized hype message.")
