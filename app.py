import streamlit as st
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="Menstrual Health & Care", page_icon="🌸", layout="centered")

# Mock Gynecologist Data (To be replaced with actual details)
GYNAE_NAME = "Dr. Jane Doe"
GYNAE_CONTACT = "+1-800-555-CARE"
GYNAE_CLINIC = "Women's Wellness Clinic, City Center"

# Red-flag keywords that trigger the medical threshold stop
MEDICAL_KEYWORDS = [
    "severe pain", "fainting", "vomiting", "bleeding for weeks", 
    "unbearable", "emergency", "fever", "infection", "cyst", "endometriosis",
    "dizzy", "fainted", "hospital"
]

# --- HELPER FUNCTIONS ---
def check_medical_guardrails(user_input):
    """Checks if the user input contains severe medical keywords."""
    input_lower = user_input.lower()
    for word in MEDICAL_KEYWORDS:
        if re.search(r'\b' + word + r'\b', input_lower):
            return True
    return False

def get_llm_response(prompt):
    """
    MOCK LLM FUNCTION: Simulates a conversational, direct AI.
    No medical disclaimers here - only direct answers and follow-up questions to 'take notes'.
    In production, the LLM System Prompt will enforce this behavior.
    """
    prompt_lower = prompt.lower()
    
    # Simulating specific conversational flows for the MVP
    if "change" in prompt_lower and "pad" in prompt_lower:
        return "Generally, it is recommended to change your pad every 4 to 8 hours to maintain good hygiene and prevent leaks or infections. However, if your flow is heavier, you might need to change it more frequently. \n\nHow would you describe your flow today? Is it light, medium, or heavy?"
    
    elif "light" in prompt_lower or "medium" in prompt_lower or "heavy" in prompt_lower:
        return "Noted! I've recorded that. Tracking your flow is a great habit. Based on your flow, I can suggest specific types of products, like higher absorbency pads or period panties. Are you looking to switch to more eco-friendly products, or are you happy with what you currently use?"
    
    else:
        return f"I understand. To give you the most accurate hygiene advice regarding '{prompt}', could you tell me a little bit more about what you usually use or how you are currently feeling?"

def search_products(query):
    """
    MOCK AGENT FUNCTION: Simulates an Agentic workflow fetching affiliate links.
    """
    products = [
        {"name": "Eco-Friendly Organic Pads", "desc": "100% organic cotton, highly absorbent, biodegradable.", "link": "https://amazon.com/mock-organic-pads"},
        {"name": "Comfort Period Panties", "desc": "Reusable, leak-proof, and great for heavy flow days.", "link": "https://flipkart.com/mock-period-panties"},
        {"name": "Menstrual Cup (Beginner Friendly)", "desc": "Medical grade silicone, safe on skin, lasts up to 10 years.", "link": "https://amazon.com/mock-cup"}
    ]
    return products

# --- UI LAYOUT ---
st.title("🌸 Menstrual Health & Care Assistant")
st.markdown("Welcome! I am here to help you with menstrual hygiene, product recommendations, and wellness tips.")

# Create tabs for the three main features
tab1, tab2, tab3 = st.tabs(["💬 Chatbot", "🛍️ Product Recommendations", "📝 Anonymous Survey"])

# --- TAB 1: GUARDRAILED CHATBOT ---
with tab1:
    st.subheader("Chat about Menstrual Hygiene")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Ask a question (e.g., 'How often should I change my pad?')"):
        # Display user message
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 1. STRICT THRESHOLD CHECK: Look for red flags FIRST
        if check_medical_guardrails(prompt):
            # The chatbot stops being conversational and triggers the hard stop
            guardrail_msg = f"**⚠️ MEDICAL THRESHOLD REACHED:** It sounds like you might be experiencing a medical issue that requires professional attention. I cannot provide medical advice or predictions for this. Please halt use of this app for this issue and consult a doctor immediately.\n\n**We strongly recommend contacting your Gynecologist:**\n* **Doctor:** {GYNAE_NAME}\n* **Contact:** {GYNAE_CONTACT}\n* **Clinic:** {GYNAE_CLINIC}"
            
            with st.chat_message("assistant"):
                st.error(guardrail_msg)
            st.session_state.messages.append({"role": "assistant", "content": guardrail_msg})
        
        # 2. CONVERSATIONAL FLOW: Proceed to normal LLM if safe
        else:
            # The LLM gives a direct answer and asks a follow-up question
            response = get_llm_response(prompt)
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# --- TAB 2: AGENTIC PRODUCT RECOMMENDER ---
with tab2:
    st.subheader("Discover Safe & Eco-Friendly Products")
    st.write("Looking for something specific? Let our AI agent find the best gynecologist-approved, skin-friendly products for you.")
    
    product_query = st.text_input("What are you looking for?", placeholder="e.g., organic pads, period panties, heating patches")
    
    if st.button("Search Products"):
        if product_query:
            with st.spinner("Agent is searching for the best products..."):
                results = search_products(product_query)
                st.success("Here are some recommended products:")
                
                for item in results:
                    with st.container():
                        st.markdown(f"### {item['name']}")
                        st.write(item['desc'])
                        st.markdown(f"[🛒 Buy Here (Affiliate Link)]({item['link']})")
                        st.divider()
        else:
            st.warning("Please enter a product to search for.")

# --- TAB 3: ANONYMOUS SURVEY ---
with tab3:
    st.subheader("Research Survey")
    st.markdown("""
    **Help us improve female hygiene products!** This survey is conducted by our lead researcher. All data collected is **100% anonymous** and will only be used to develop better, safer menstrual health products.
    """)
    
    with st.form("survey_form"):
        age_group = st.selectbox("Age Group", ["Under 18", "18-24", "25-34", "35-44", "45+"])
        primary_product = st.selectbox("Primary Menstrual Product Used", ["Pads", "Tampons", "Menstrual Cups", "Period Panties", "Other"])
        comfort_level = st.slider("How comfortable are you with your current products?", 1, 10, 5)
        issues = st.text_area("Do you face any specific issues? (e.g., rashes, leaks) - Optional")
        
        # Explicit Consent Checkbox
        consent = st.checkbox("I consent to sharing this anonymous data for research purposes.")
        
        submitted = st.form_submit_button("Submit Survey")
        
        if submitted:
            if consent:
                st.success("Thank you! Your anonymous response has been recorded.")
            else:
                st.error("Please provide consent to submit the form.")
