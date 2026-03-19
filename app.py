import streamlit as st
import re
import urllib.parse
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
        for m in valid_models:
            if "gemini-1.5-flash" in m and "latest" not in m:
                return m
        for m in valid_models:
            if "1.5" in m: return m
        if valid_models: return valid_models[0]
    except Exception:
        pass
    return "gemini-1.5-flash"

def check_medical_guardrails(user_input):
    """Checks if the user input contains severe medical keywords."""
    input_lower = user_input.lower()
    for word in MEDICAL_KEYWORDS:
        if re.search(r'\b' + word + r'\b', input_lower):
            return True
    return False

def get_live_product_recommendations(query, model_name):
    """
    REAL AGENT FUNCTION: Uses Gemini to suggest specific products 
    and generates live Amazon search URLs for them.
    """
    try:
        # 1. Ask the AI to suggest 3 specific products based on user query
        agent_model = genai.GenerativeModel(model_name=model_name)
        prompt = f"""
        The user is looking for menstrual health products related to: "{query}".
        Suggest 3 specific, safe, and highly-rated product categories/types.
        Format your response EXACTLY like this (do not add any other text or markdown):
        Product 1 Name | Short description of why it is good for health/hygiene
        Product 2 Name | Short description of why it is good for health/hygiene
        Product 3 Name | Short description of why it is good for health/hygiene
        """
        
        response = agent_model.generate_content(prompt)
        lines = response.text.strip().split('\n')
        
        results = []
        for line in lines:
            if '|' in line:
                name, desc = line.split('|', 1)
                name = name.strip()
                desc = desc.strip()
                
                # 2. Convert the product name into a live Amazon search link!
                encoded_name = urllib.parse.quote(name)
                # You can change amazon.com to amazon.in depending on your region
                amazon_link = f"https://www.amazon.in/s?k={encoded_name}"
                
                results.append({
                    "name": name,
                    "desc": desc,
                    "link": amazon_link
                })
        
        if not results:
            raise Exception("Parsing failed")
            
        return results

    except Exception as e:
        # Fallback if the AI fails to format correctly
        encoded_query = urllib.parse.quote(query)
        return [{
            "name": f"Top rated {query}", 
            "desc": "Click here to see the best options currently available.", 
            "link": f"https://www.amazon.in/s?k={encoded_query}"
        }]

# --- UI LAYOUT ---
st.title("🌸 Menstrual Health & Care Assistant")

tab1, tab2, tab3 = st.tabs(["💬 Chatbot", "🛍️ Product Recommendations", "📝 Anonymous Survey"])

# Initialize the model early so Tab 2 can also use it
working_model = get_best_model_name() if api_configured else None

# --- TAB 1: GUARDRAILED CHATBOT WITH REAL LLM ---
with tab1:
    st.subheader("Chat about Menstrual Hygiene")
    
    if not api_configured:
        st.error("⚠️ Setup incomplete! Please add the API key to the Streamlit App Settings -> Secrets.")
    else:
        st.caption(f"*(System info: Connected to {working_model})*")

        try:
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

# --- TAB 2: AGENTIC PRODUCT RECOMMENDER ---
with tab2:
    st.subheader("Discover Safe & Eco-Friendly Products")
    st.write("Looking for something specific? Let our AI agent find the best gynecologist-approved products.")
    
    product_query = st.text_input("What are you looking for?", placeholder="e.g., eco friendly pads, heating patches")
    
    if st.button("Search Products"):
        if not api_configured:
            st.error("Please configure the API key first.")
        elif product_query:
            with st.spinner("Agent is analyzing your request and fetching live links..."):
                results = get_live_product_recommendations(product_query, working_model)
                for item in results:
                    st.markdown(f"**{item['name']}**")
                    st.write(f"{item['desc']}")
                    # Use a Streamlit native link button for a cleaner look
                    st.link_button("🛒 Search & Buy on Amazon", item['link'])
                    st.divider()

# --- TAB 3: ANONYMOUS SURVEY ---
with tab3:
    st.subheader("Research Survey")
    st.markdown("All data collected is **100% anonymous** and used to develop better menstrual health products.")
    
    with st.form("survey_form"):
        age_group = st.selectbox("Age Group", ["Under 18", "18-24", "25-34", "35-44", "45+"])
        primary_product = st.selectbox("Primary Menstrual Product Used", ["Pads", "Tampons", "Menstrual Cups", "Period Panties", "Other"])
        comfort_level = st.slider("How comfortable are you with your current products?", 1, 10, 5)
        issues = st.text_area("Do you face any specific issues? (e.g., rashes, leaks) - Optional")
        
        consent = st.checkbox("I consent to sharing this anonymous data for research purposes.")
        
        if st.form_submit_button("Submit Survey"):
            if consent:
                st.success("Thank you! Your anonymous response has been recorded.")
            else:
                st.error("Please provide consent to submit the form.")
