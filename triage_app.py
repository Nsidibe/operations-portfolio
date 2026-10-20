import os
import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv

# --- SETUP ---
load_dotenv()
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

st.set_page_config(page_title="Support Triage System", page_icon="🎫", layout="centered")
st.title("🎫 Automated Support Ticket Triage")
st.markdown("Instantly classify incoming customer queries, route them to the right team, and generate a draft response.")

# --- MAIN UI ---
st.info("💡 **Try this example:** 'I was charged twice for my subscription this month and I need a refund immediately! My account is locked and I am losing money.'")

ticket_text = st.text_area("Paste Incoming Customer Ticket:", height=150)

if st.button("Triage & Route Ticket", type="primary"):
    if not ticket_text:
        st.warning("Please paste a ticket to analyze.")
    else:
        with st.spinner("Analyzing ticket severity and routing..."):
            prompt = f"""
            You are an expert Customer Operations AI. Analyze the following customer support ticket.
            
            Customer Ticket:
            "{ticket_text}"
            
            Provide your response in exactly three sections using Markdown formatting:
            
            ### 🏷️ Classification
            State the Primary Category (e.g., Billing, Technical, Feedback, Login Issue) and the Urgency (Low, Medium, High, Critical).
            
            ### 🔀 Routing
            State which specific department this should be routed to, and give a 1-sentence reason why.
            
            ### ✉️ Draft Response
            Write a professional, empathetic first-touch email response addressing the customer's issue. Leave placeholders like [Name] where appropriate.
            """

            try:
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                result = next((block.text for block in response.content if block.type == "text"), None)
                
                if result:
                    st.success("Ticket successfully triaged!")
                    st.markdown(result)
                else:
                    st.error("Failed to generate triage report.")
                    
            except Exception as e:
                st.error(f"API Error: {e}")