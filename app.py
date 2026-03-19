import streamlit as st
import re
import google.generativeai as genai

# --- CONFIGURATION ---
st.set_page_config(page_title="Menstrual Health & Care", page_icon="🌸", layout="centered")

# Securely fetch the API key from Streamlit Secrets
api_configured = False
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    api_configured = True
except Exception as e:
    st.sidebar.error("API Key not found in Streamlit Secrets. Please configure it in the app settings.")

# Mock Gynecologist Data
GYNAE_NAME = "Dr. Jane Doe"
GYNAE_CONTACT = "+1-800-555-CARE"
GYNAE_CLINIC = "Women's Wellness Clinic, City Center"

# Red-flag keywords that trigger the hard medical stop
MEDICAL_KEYWORDS = [
    "severe pain", "fainting", "vomiting", "bleeding for weeks", 
    "unbearable", "emergency", "fever", "infection", "cyst", "endometriosis",
    "dizzy", "fainted", "hospital", "painkiller not working"
]

# --- AI SETUP & SYSTEM PROMPT ---
SYSTEM_INSTRUCTION = """
You are an empathetic, highly knowledgeable menstrual health and hygiene assistant.
Strict Rules you MUST follow:
1. Answer the user's hygiene or product question directly and concisely.
2. NEVER include medical disclaimers, warnings, or tell the user to consult a doctor. The system handles medical emergencies separately.
3. ALWAYS end your response with exactly ONE relevant follow-up question to "take notes" and understand their specific needs, cycle, or preferences better.
4. If they mention discomfort, ask about the specific product they are using so you can note it down.
5. Maintain a warm, supportive, and conversational tone.
"""

# --- HELPER FUNCTIONS ---
@st.cache_resource
def get_best_model_name():
    """Dynamically fetches the best available model for this specific API key."""
    try:
        valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Try to find a 1.5 flash model first (fastest and supports system instructions)
        for m in valid_models:
            if "gemini-1.5-flash" in m and "latest" not in m:
                return m
        
        # Fallback to any 1.5 model
        for m in valid_models:
            if "1.5" in m:
                return m
                
        # Absolute fallback
        if valid_models:
            return valid_models[0]
            
    except Exception as e:
        return "gemini-1.5-flash" # Default fallback if listing fails
        
    return "gemini-1.5-flash"

def check_medical_guardrails(user_input):
    """Checks if the user input contains severe medical keywords."""
    input_lower = user_input.lower()
    for word in MEDICAL_KEYWORDS:
        if re.search(r'\b' + word + r'\b', input_lower):
            return True
    return False

def search_products(query):
    """Mock Agent Function: Returns curated affiliate links based on query"""
    products = [
        {"name": "Eco-Friendly Organic Pads", "desc": "100% organic cotton, highly absorbent, biodegradable.", "link": "https://amazon.com/mock-organic-pads"},
        {"name": "Comfort Period Panties", "desc": "Reusable, leak-proof, and great for heavy flow days.", "link": "https://flipkart.com/mock-period-panties"},
        {"name": "Menstrual Cup (Beginner Friendly)", "desc": "Medical grade silicone, safe on skin, lasts up to 10 years.", "link": "https://amazon.com/mock-cup"}
    ]
    return products

# --- UI LAYOUT ---
st.title("🌸 Menstrual Health & Care Assistant")

tab1, tab2, tab3 = st.tabs(["💬 Chatbot", "🛍️ Product Recommendations", "📝 Anonymous Survey"])

# --- TAB 1: GUARDRAILED CHATBOT WITH REAL LLM ---
with tab1:
    st.subheader("Chat about Menstrual Hygiene")
    
    if not api_configured:
        st.error("⚠️ Setup incomplete! Please add the API key to the Streamlit App Settings -> Secrets.")
    else:
        # 1. Automatically detect the correct model
        working_model = get_best_model_name()
        st.caption(f"*(System info: Connected to {working_model})*")

        # 2. Initialize the Gemini Model safely
        try:
            # Check if the chosen model is an older one that doesn't support system instructions
            if "1.5" in working_model or "2.0" in working_model:
                model = genai.GenerativeModel(model_name=working_model, system_instruction=SYSTEM_INSTRUCTION)
            else:
                model = genai.GenerativeModel(model_name=working_model)
        except Exception as e:
            st.error(f"Failed to initialize model: {e}")

        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
            
        # Initialize Gemini Chat Session (for memory)
        if "chat_session" not in st.session_state:
            try:
                st.session_state.chat_session = model.start_chat(history=[])
            except Exception as e:
                st.error("Failed to start chat session. Please refresh the page.")

        # Display UI chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # React to user input
        if prompt := st.chat_input("Ask a question (e.g., 'How often should I change my pad?')"):
            
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            # STRICT THRESHOLD CHECK
            if check_medical_guardrails(prompt):
                guardrail_msg = f"**⚠️ MEDICAL THRESHOLD REACHED:** It sounds like you might be experiencing a medical issue that requires professional attention. I cannot provide medical advice for this. Please halt use of this app for this issue and consult a doctor immediately.\n\n**We strongly recommend contacting your Gynecologist:**\n* **Doctor:** {GYNAE_NAME}\n* **Contact:** {GYNAE_CONTACT}\n* **Clinic:** {GYNAE_CLINIC}"
                
                with st.chat_message("assistant"):
                    st.error(guardrail_msg)
                st.session_state.messages.append({"role": "assistant", "content": guardrail_msg})
            
            # REAL LLM CONVERSATION FLOW
            else:
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            response = st.session_state.chat_session.send_message(prompt)
                            st.markdown(response.text)
                            st.session_state.messages.append({"role": "assistant", "content": response.text})
                        except Exception as e:
                            st.error(f"Google API Error: {e}")

# --- TAB 2 & 3 (Unchanged) ---
with tab2:
    st.subheader("Discover Safe & Eco-Friendly Products")
    product_query = st.text_input("What are you looking for?", placeholder="e.g., organic pads, heating patches")
    if st.button("Search Products"):
        if product_query:
            results = search_products(product_query)
            for item in results:
                st.markdown(f"**{item['name']}** - {item['desc']} [🛒 Buy Here]({item['link']})")
                st.divider()

with tab3:
    st.subheader("Research Survey")
    with st.form("survey_form"):
        age_group = st.selectbox("Age Group", ["Under 18", "18-24", "25-34", "35-44", "45+"])
        primary_product = st.selectbox("Primary Menstrual Product Used", ["Pads", "Tampons", "Menstrual Cups", "Period Panties"])
        consent = st.checkbox("I consent to sharing this anonymous data for research purposes.")
        if st.form_submit_button("Submit Survey"):
            if consent: st.success("Thank you! Your anonymous response has been recorded.")
            else: st.error("Please provide consent to submit the form.")
